-- =====================================================================
-- 04_atualizacao_remocao.sql  |  UPDATE, DELETE e transações
-- Os testes de remoção usam registros temporários criados aqui, para não
-- apagar os dados de demonstração.
-- =====================================================================
\pset border 2

\echo '--- U1 (RF04) Administrador avança o status da solicitação mais recente: solicitado -> coletado'
UPDATE solicitacao_descarte
   SET status = 'coletado',
       atualizado_por_id = (SELECT id FROM usuario WHERE email = 'admin@exemplo.com')
 WHERE data = '2026-11-03'
RETURNING id, status, atualizado_por_id;

\echo '--- U2 (RF05) Administrador corrige o horário de um ponto de coleta'
UPDATE ponto_coleta
   SET horario = 'Seg a sex, 8h às 17h; sáb, 8h às 12h'
 WHERE nome LIKE 'Ponto de coleta da sede%'
RETURNING id, nome, horario;

\echo '--- U3 Cadastro de registros temporários (unidade, usuário, ponto, solicitação e item)'
INSERT INTO unidade (nome, tipo, cidade) VALUES ('Unidade temporária (teste)', 'loja', 'Campo Grande');
INSERT INTO usuario (nome, email, senha_hash, unidade_id)
     VALUES ('Usuário temporário', 'temporario@exemplo.com', '!exemplo-sem-senha',
             (SELECT id FROM unidade WHERE nome = 'Unidade temporária (teste)'));
INSERT INTO ponto_coleta (nome, endereco) VALUES ('Ponto temporário (teste)', 'Endereço de teste, 1');
INSERT INTO ponto_tipo (ponto_id, tipo_id)
     SELECT p.id, t.id FROM ponto_coleta p, tipo_residuo t
      WHERE p.nome = 'Ponto temporário (teste)' AND t.nome IN ('Pilhas', 'Celulares');
INSERT INTO solicitacao_descarte (usuario_id, unidade_id, ponto_id, data)
     SELECT u.id, u.unidade_id, p.id, '2026-11-04'
       FROM usuario u, ponto_coleta p
      WHERE u.email = 'temporario@exemplo.com' AND p.nome = 'Ponto temporário (teste)';
INSERT INTO item_descartado (solicitacao_id, tipo_id, quantidade)
     SELECT s.id, t.id, 2
       FROM solicitacao_descarte s, tipo_residuo t
      WHERE s.data = '2026-11-04' AND t.nome = 'Pilhas';
SELECT count(*) AS itens_temporarios
  FROM item_descartado i JOIN solicitacao_descarte s ON s.id = i.solicitacao_id WHERE s.data = '2026-11-04';

\echo '--- U4 Atualização de quantidade e de observação de um item'
UPDATE item_descartado i
   SET quantidade = 3, observacao = 'Pilhas AA'
  FROM solicitacao_descarte s
 WHERE s.id = i.solicitacao_id AND s.data = '2026-11-04'
RETURNING i.id, i.quantidade, i.observacao;

\echo '--- D1 Transação revertida: apaga os itens, confere e desfaz com ROLLBACK'
BEGIN;
DELETE FROM item_descartado WHERE solicitacao_id IN (SELECT id FROM solicitacao_descarte WHERE data = '2026-11-04');
SELECT count(*) AS itens_dentro_da_transacao
  FROM item_descartado i JOIN solicitacao_descarte s ON s.id = i.solicitacao_id WHERE s.data = '2026-11-04';
ROLLBACK;
SELECT count(*) AS itens_apos_rollback
  FROM item_descartado i JOIN solicitacao_descarte s ON s.id = i.solicitacao_id WHERE s.data = '2026-11-04';

\echo '--- D2 Remoção em cascata: apagar a solicitação apaga seus itens (ON DELETE CASCADE)'
DELETE FROM solicitacao_descarte WHERE data = '2026-11-04' RETURNING id;
SELECT count(*) AS itens_orfaos
  FROM item_descartado i LEFT JOIN solicitacao_descarte s ON s.id = i.solicitacao_id WHERE s.id IS NULL;

\echo '--- D3 Remoção do ponto temporário: apaga também as linhas de ponto_tipo (CASCADE)'
DELETE FROM ponto_coleta WHERE nome = 'Ponto temporário (teste)';
SELECT count(*) AS ligacoes_restantes_do_ponto_removido
  FROM ponto_tipo pt LEFT JOIN ponto_coleta p ON p.id = pt.ponto_id WHERE p.id IS NULL;

\echo '--- D4 Remoção da unidade temporária: o usuário permanece e fica sem unidade (SET NULL)'
DELETE FROM unidade WHERE nome = 'Unidade temporária (teste)';
SELECT email, unidade_id FROM usuario WHERE email = 'temporario@exemplo.com';

\echo '--- D5 Remoção do usuário temporário'
DELETE FROM usuario WHERE email = 'temporario@exemplo.com' RETURNING id, email;
