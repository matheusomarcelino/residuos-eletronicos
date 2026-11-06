-- =====================================================================
-- 03_consultas.sql  |  Consultas (SELECT)
-- Cada consulta indica o requisito do sistema que ela atende.
-- =====================================================================
\pset border 2

\echo '--- C1 (RF03) Pontos de coleta ativos e os tipos que aceitam'
SELECT p.nome AS ponto,
       p.horario,
       string_agg(t.nome, ', ' ORDER BY t.nome) AS tipos_aceitos
FROM ponto_coleta p
LEFT JOIN ponto_tipo pt ON pt.ponto_id = p.id
LEFT JOIN tipo_residuo t ON t.id = pt.tipo_id
WHERE p.ativo
GROUP BY p.id, p.nome, p.horario
ORDER BY p.nome;

\echo '--- C2 (RF03) Filtro: pontos que aceitam "Pilhas"'
SELECT p.nome AS ponto, p.endereco
FROM ponto_coleta p
JOIN ponto_tipo pt ON pt.ponto_id = p.id
JOIN tipo_residuo t ON t.id = pt.tipo_id
WHERE p.ativo AND t.nome = 'Pilhas'
ORDER BY p.nome;

\echo '--- C3 (RF04/RF06) Solicitações com usuário, unidade, ponto e total de itens (visão)'
SELECT id, data, status, usuario, unidade, ponto, total_itens
FROM v_solicitacoes_detalhe
ORDER BY data DESC, id DESC;

\echo '--- C4 (RF04) Solicitações ainda não encaminhadas (pendentes de ação do administrador)'
SELECT s.id, s.data, s.status, un.nome AS unidade
FROM solicitacao_descarte s
JOIN unidade un ON un.id = s.unidade_id
WHERE s.status <> 'encaminhado'
ORDER BY s.data;

\echo '--- C5 (RF07) Total de itens por tipo, com percentual (visão com função de janela)'
SELECT tipo, total, percentual
FROM v_total_por_tipo
ORDER BY total DESC, tipo;

\echo '--- C6 (RF07) Total de itens por unidade'
SELECT un.nome AS unidade, SUM(i.quantidade) AS total_itens, COUNT(DISTINCT s.id) AS solicitacoes
FROM solicitacao_descarte s
JOIN unidade un ON un.id = s.unidade_id
JOIN item_descartado i ON i.solicitacao_id = s.id
GROUP BY un.nome
ORDER BY total_itens DESC;

\echo '--- C7 (RF07) Total de itens por mês'
SELECT to_char(date_trunc('month', s.data), 'YYYY-MM') AS mes, SUM(i.quantidade) AS total_itens
FROM solicitacao_descarte s
JOIN item_descartado i ON i.solicitacao_id = s.id
GROUP BY date_trunc('month', s.data)
ORDER BY mes;

\echo '--- C8 Tipos de resíduo que ainda não foram descartados (LEFT JOIN ... IS NULL)'
SELECT t.nome AS tipo
FROM tipo_residuo t
LEFT JOIN item_descartado i ON i.tipo_id = t.id
WHERE i.id IS NULL;

\echo '--- C9 Pontos que aceitam TODOS os tipos cadastrados (divisão relacional com HAVING)'
SELECT p.nome
FROM ponto_coleta p
JOIN ponto_tipo pt ON pt.ponto_id = p.id
GROUP BY p.id, p.nome
HAVING COUNT(*) = (SELECT COUNT(*) FROM tipo_residuo)
ORDER BY p.nome;

\echo '--- C10 (RF08) Orientações de descarte de um tipo'
SELECT nome, orientacoes FROM tipo_residuo WHERE nome = 'Celulares';
