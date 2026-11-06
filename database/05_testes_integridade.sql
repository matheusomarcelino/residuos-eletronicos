-- =====================================================================
-- 05_testes_integridade.sql  |  Testes das restrições e dos gatilhos
-- Cada bloco tenta uma operação INVÁLIDA e confere se o banco a rejeitou.
-- Saída: "OK" quando a operação foi rejeitada como esperado; "FALHOU" se o banco aceitou.
-- Tudo roda dentro de uma transação revertida (ROLLBACK): nada fica gravado.
-- =====================================================================
\set ON_ERROR_STOP on
BEGIN;

CREATE TEMP TABLE resultado_testes (n int, descricao text, esperado text, obtido text, situacao text);

CREATE OR REPLACE FUNCTION pg_temp.tentar(p_n int, p_desc text, p_sql text, p_esperado text) RETURNS void AS $$
DECLARE v_estado text;
BEGIN
    BEGIN
        EXECUTE p_sql;
        INSERT INTO resultado_testes VALUES (p_n, p_desc, p_esperado, 'aceito (sem erro)', 'FALHOU');
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_estado = RETURNED_SQLSTATE;
        INSERT INTO resultado_testes VALUES (p_n, p_desc, p_esperado,
            CASE v_estado WHEN '23505' THEN 'unique_violation' WHEN '23503' THEN 'foreign_key_violation'
                          WHEN '23502' THEN 'not_null_violation' WHEN '23514' THEN 'check_violation'
                          ELSE v_estado END,
            CASE WHEN (v_estado = '23505' AND p_esperado = 'unique_violation')
                   OR (v_estado = '23503' AND p_esperado = 'foreign_key_violation')
                   OR (v_estado = '23502' AND p_esperado = 'not_null_violation')
                   OR (v_estado = '23514' AND p_esperado = 'check_violation') THEN 'OK' ELSE 'FALHOU' END);
    END;
END;
$$ LANGUAGE plpgsql;

\o /dev/null
SELECT pg_temp.tentar(1,  'Unidade com nome repetido',
  $q$INSERT INTO unidade (nome) VALUES ('Loja Exemplo Centro')$q$, 'unique_violation');
SELECT pg_temp.tentar(2,  'Unidade com tipo inválido',
  $q$INSERT INTO unidade (nome, tipo) VALUES ('X', 'galpao')$q$, 'check_violation');
SELECT pg_temp.tentar(3,  'Usuário com e-mail repetido',
  $q$INSERT INTO usuario (nome, email, senha_hash) VALUES ('Outro', 'admin@exemplo.com', '!x')$q$, 'unique_violation');
SELECT pg_temp.tentar(4,  'Usuário com e-mail em formato inválido',
  $q$INSERT INTO usuario (nome, email, senha_hash) VALUES ('Outro', 'sem-arroba', '!x')$q$, 'check_violation');
SELECT pg_temp.tentar(5,  'Usuário com perfil inexistente',
  $q$INSERT INTO usuario (nome, email, senha_hash, perfil) VALUES ('Outro', 'a@b.com', '!x', 'chefe')$q$, 'check_violation');
SELECT pg_temp.tentar(6,  'Usuário sem nome (NOT NULL)',
  $q$INSERT INTO usuario (nome, email, senha_hash) VALUES (NULL, 'c@d.com', '!x')$q$, 'not_null_violation');
SELECT pg_temp.tentar(7,  'Usuário apontando para unidade inexistente (FK)',
  $q$INSERT INTO usuario (nome, email, senha_hash, unidade_id) VALUES ('Outro', 'e@f.com', '!x', 9999)$q$, 'foreign_key_violation');
SELECT pg_temp.tentar(8,  'Tipo de resíduo com nome repetido',
  $q$INSERT INTO tipo_residuo (nome) VALUES ('Pilhas')$q$, 'unique_violation');
SELECT pg_temp.tentar(9,  'Ligação ponto–tipo repetida (chave composta)',
  $q$INSERT INTO ponto_tipo SELECT ponto_id, tipo_id FROM ponto_tipo LIMIT 1$q$, 'unique_violation');
SELECT pg_temp.tentar(10, 'Solicitação com data no futuro',
  $q$INSERT INTO solicitacao_descarte (usuario_id, unidade_id, ponto_id, data)
     SELECT u.id, u.unidade_id, p.id, CURRENT_DATE + 1 FROM usuario u, ponto_coleta p LIMIT 1$q$, 'check_violation');
SELECT pg_temp.tentar(11, 'Solicitação criada já como "coletado" (gatilho do fluxo)',
  $q$INSERT INTO solicitacao_descarte (usuario_id, unidade_id, ponto_id, status)
     SELECT u.id, u.unidade_id, p.id, 'coletado' FROM usuario u, ponto_coleta p LIMIT 1$q$, 'check_violation');
SELECT pg_temp.tentar(12, 'Solicitação com status fora da lista',
  $q$UPDATE solicitacao_descarte SET status = 'perdido' WHERE id = (SELECT min(id) FROM solicitacao_descarte)$q$, 'check_violation');
SELECT pg_temp.tentar(13, 'Pular etapa: solicitado -> encaminhado',
  $q$DO $x$
     DECLARE v_id int;
     BEGIN
       INSERT INTO solicitacao_descarte (usuario_id, unidade_id, ponto_id)
         SELECT u.id, u.unidade_id, p.id FROM usuario u, ponto_coleta p LIMIT 1 RETURNING id INTO v_id;
       UPDATE solicitacao_descarte SET status = 'encaminhado' WHERE id = v_id;
     END $x$$q$, 'check_violation');
SELECT pg_temp.tentar(14, 'Voltar etapa: encaminhado -> solicitado',
  $q$UPDATE solicitacao_descarte SET status = 'solicitado' WHERE status = 'encaminhado'$q$, 'check_violation');
SELECT pg_temp.tentar(15, 'Item com quantidade zero',
  $q$INSERT INTO item_descartado (solicitacao_id, tipo_id, quantidade)
     SELECT (SELECT min(id) FROM solicitacao_descarte), (SELECT min(id) FROM tipo_residuo), 0$q$, 'check_violation');
SELECT pg_temp.tentar(16, 'Item de um tipo que o ponto não aceita (gatilho)',
  $q$INSERT INTO item_descartado (solicitacao_id, tipo_id, quantidade)
     SELECT s.id, (SELECT id FROM tipo_residuo WHERE nome = 'Celulares'), 1
       FROM solicitacao_descarte s JOIN ponto_coleta p ON p.id = s.ponto_id
      WHERE p.nome LIKE 'Ponto de coleta de pilhas%' LIMIT 1$q$, 'check_violation');
SELECT pg_temp.tentar(17, 'Item de solicitação inexistente (FK)',
  $q$INSERT INTO item_descartado (solicitacao_id, tipo_id) VALUES (9999, 1)$q$, 'foreign_key_violation');
SELECT pg_temp.tentar(18, 'Apagar tipo de resíduo já usado em itens (RESTRICT)',
  $q$DELETE FROM tipo_residuo WHERE nome = 'Pilhas'$q$, 'foreign_key_violation');
SELECT pg_temp.tentar(19, 'Apagar ponto de coleta com solicitações (RESTRICT)',
  $q$DELETE FROM ponto_coleta WHERE nome LIKE 'Ponto de coleta da sede%'$q$, 'foreign_key_violation');
SELECT pg_temp.tentar(20, 'Apagar usuário que registrou solicitações (RESTRICT)',
  $q$DELETE FROM usuario WHERE email = 'colaborador@exemplo.com'$q$, 'foreign_key_violation');

\o
\pset border 2
SELECT n AS "nº", descricao AS "tentativa inválida", esperado, obtido, situacao AS "resultado" FROM resultado_testes ORDER BY n;
SELECT count(*) FILTER (WHERE situacao = 'OK') AS aprovados,
       count(*) FILTER (WHERE situacao <> 'OK') AS falharam,
       count(*) AS total
FROM resultado_testes;

ROLLBACK;
