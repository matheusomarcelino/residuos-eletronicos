# Banco de dados (SQL) – PostgreSQL

Scripts do Módulo 3 do PI II. Eles modelam, em SQL puro, as mesmas entidades do sistema web (DER em
`docs/diagramas/der_sql.png`) e mostram as operações de inserção, consulta, atualização e remoção.

| Arquivo | O que faz |
|---|---|
| `01_schema.sql` | Cria tabelas, chaves primárias e estrangeiras, restrições (UNIQUE, NOT NULL, CHECK), índices, 3 gatilhos e 2 visões |
| `02_dados.sql` | INSERT dos dados de demonstração (inclui o Recic.LE) e avanço de status |
| `03_consultas.sql` | 10 consultas SELECT (junções, agregações, filtros, visões, função de janela) |
| `04_atualizacao_remocao.sql` | UPDATE, DELETE, transação com ROLLBACK e efeitos de CASCADE e SET NULL |
| `05_testes_integridade.sql` | 20 tentativas inválidas que o banco precisa rejeitar |
| `executar.sh` | Recria o banco `descarte` e roda os cinco scripts em ordem |

## Como executar

Pré-requisito: PostgreSQL 14 ou superior com o cliente `psql` (testado na versão 16).

```bash
cd database
bash executar.sh               # Linux/macOS; usa as variáveis PGUSER, PGHOST, PGPORT se necessário
```

No Windows, abra o *SQL Shell (psql)* instalado com o PostgreSQL e rode, dentro da pasta `database`:

```
CREATE DATABASE descarte;
\c descarte
\i 01_schema.sql
\i 02_dados.sql
\i 03_consultas.sql
\i 04_atualizacao_remocao.sql
\i 05_testes_integridade.sql
```

O resultado de uma execução real está em `docs/testes/saida_execucao_sql.txt`.

## Observações
- Os scripts são independentes do Django: o sistema web continua usando SQLite e as tabelas `descarte_*`
  criadas pelas migrações. As diferenças entre os dois estão em `docs/BANCO_DE_DADOS.md`.
- As contas de exemplo usam o hash `!exemplo-sem-senha` e não permitem login.
- Dois dos três pontos de coleta e as unidades são fictícios; o Recic.LE usa dados informados pelo autor
  e deve ser reconfirmado com a associação.
