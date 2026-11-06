-- =====================================================================
-- 02_dados.sql  |  Inserção de dados (INSERT) – dados de DEMONSTRAÇÃO
-- Equivale ao comando "seed_demo" do sistema web. As contas não têm senha utilizável
-- (o marcador "!" no hash é a convenção do Django para "sem senha"). Os pontos
-- "(exemplo)" são fictícios; o Recic.LE usa endereço e horários informados pelo autor
-- e deve ser reconfirmado com a associação.
-- =====================================================================

INSERT INTO unidade (nome, tipo, cidade) VALUES
    ('Sede – Tecnologia da Informação', 'setor', 'Campo Grande'),
    ('Loja Exemplo Centro',             'loja',  'Campo Grande'),
    ('Loja Exemplo Bairro',             'loja',  'Campo Grande');

INSERT INTO tipo_residuo (nome, orientacoes) VALUES
    ('Pilhas',    'Não descarte no lixo comum. Entregue em ponto de coleta; mantenha as pilhas secas e separadas.'),
    ('Baterias',  'Evite perfurar ou amassar. Se estiver estufada, isole e entregue com cuidado em ponto de coleta.'),
    ('Celulares', 'Apague os dados e saia das contas antes de descartar. Retire o chip e o cartão de memória.'),
    ('Carregadores e cabos',       'Entregue junto com os demais eletrônicos; podem ser reaproveitados ou reciclados.'),
    ('Computadores e periféricos', 'Apague ou destrua o armazenamento (HD/SSD) com segurança antes de entregar.');

INSERT INTO ponto_coleta (nome, endereco, horario) VALUES
    ('Ponto de coleta da sede (exemplo)',
     'Endereço de exemplo, 100 – Campo Grande/MS', 'Seg a sex, 8h às 17h'),
    ('Ponto de coleta de pilhas e baterias (exemplo)',
     'Endereço de exemplo, 200 – Campo Grande/MS', 'Seg a sáb, 9h às 18h'),
    ('Recic.LE – Associação dos Recicladores de Resíduos Eletroeletrônicos',
     'Rua Vera Cruz, 542 – Bairro Rita Vieira, Campo Grande/MS',
     'Seg a sex, 8h às 18h; sáb, 8h às 12h; dom fechado');

-- Relação N:N: o ponto da sede e o Recic.LE aceitam todos os tipos; o outro, só pilhas e baterias.
INSERT INTO ponto_tipo (ponto_id, tipo_id)
SELECT p.id, t.id
FROM ponto_coleta p CROSS JOIN tipo_residuo t
WHERE p.nome LIKE 'Ponto de coleta da sede%' OR p.nome LIKE 'Recic.LE%';

INSERT INTO ponto_tipo (ponto_id, tipo_id)
SELECT p.id, t.id
FROM ponto_coleta p JOIN tipo_residuo t ON t.nome IN ('Pilhas', 'Baterias')
WHERE p.nome LIKE 'Ponto de coleta de pilhas%';

INSERT INTO usuario (nome, email, senha_hash, unidade_id, perfil) VALUES
    ('Administrador Exemplo', 'admin@exemplo.com',       '!exemplo-sem-senha',
        (SELECT id FROM unidade WHERE nome LIKE 'Sede%'), 'administrador'),
    ('Colaborador Exemplo',   'colaborador@exemplo.com', '!exemplo-sem-senha',
        (SELECT id FROM unidade WHERE nome = 'Loja Exemplo Centro'), 'colaborador');

-- Três solicitações (todas nascem "solicitado": o gatilho exige isso).
INSERT INTO solicitacao_descarte (usuario_id, unidade_id, ponto_id, data)
SELECT (SELECT id FROM usuario WHERE email = 'colaborador@exemplo.com'),
       (SELECT id FROM unidade WHERE nome = v.unidade),
       (SELECT id FROM ponto_coleta WHERE nome LIKE v.ponto),
       v.data::date
FROM (VALUES
    ('Loja Exemplo Centro', 'Ponto de coleta da sede%',       '2026-10-26'),
    ('Loja Exemplo Centro', 'Ponto de coleta de pilhas%',     '2026-10-31'),
    ('Loja Exemplo Bairro', 'Ponto de coleta da sede%',       '2026-11-03')
) AS v(unidade, ponto, data);

INSERT INTO item_descartado (solicitacao_id, tipo_id, quantidade)
SELECT s.id, t.id, v.qtd
FROM (VALUES
    ('2026-10-26', 'Celulares', 3),
    ('2026-10-26', 'Carregadores e cabos', 5),
    ('2026-10-31', 'Pilhas', 20),
    ('2026-10-31', 'Baterias', 4),
    ('2026-11-03', 'Computadores e periféricos', 2)
) AS v(data, tipo, qtd)
JOIN solicitacao_descarte s ON s.data = v.data::date
JOIN tipo_residuo t ON t.nome = v.tipo;

-- Avanço de status feito pelo administrador (as duas primeiras solicitações já andaram).
UPDATE solicitacao_descarte
   SET status = 'coletado', atualizado_por_id = (SELECT id FROM usuario WHERE email = 'admin@exemplo.com')
 WHERE data IN ('2026-10-26', '2026-10-31');
UPDATE solicitacao_descarte
   SET status = 'encaminhado', atualizado_por_id = (SELECT id FROM usuario WHERE email = 'admin@exemplo.com')
 WHERE data = '2026-10-26';
