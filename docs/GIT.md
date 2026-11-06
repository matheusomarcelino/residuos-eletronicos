# Controle de versão – estratégia usada

## Fluxo de trabalho
- **`main`**: sempre estável (o que está publicado e funcionando).
- **Branches de trabalho** (uma por assunto), criadas a partir da `main`:
  `feature/esquema-banco`, `feature/consultas-sql`, `feature/testes-integridade` e `docs/banco-de-dados`.
- **Integração:** cada branch volta para a `main` com `git merge --no-ff`, que registra o ponto de junção no histórico.
- **Versões:** tag anotada em formato `vMAJOR.MINOR.PATCH` (versionamento semântico). A entrega do PI II M2 é a base;
  o Módulo 3 gera a `v1.1.0`.

## Padrão das mensagens de commit
Segue o formato do *Conventional Commits 1.0.0*: `tipo(escopo): descrição curta no imperativo`.

| Tipo | Quando usar | Exemplo |
|---|---|---|
| `feat` | nova funcionalidade ou nova parte do sistema | `feat(banco): cria esquema SQL com chaves e restrições` |
| `test` | testes | `test(banco): adiciona 20 testes de integridade` |
| `docs` | documentação | `docs(banco): documenta dicionário de dados e normalização` |
| `fix` | correção | `fix(banco): corrige teste 13 que dependia de dados anteriores` |

## Comandos úteis
```bash
git status                                  # o que mudou
git log --oneline --graph --decorate --all  # histórico com branches e merges
git diff                                    # diferenças ainda não registradas
git checkout main && git pull               # voltar à main e atualizar
```

## Cuidados
- Um commit por mudança lógica, com mensagem que explique o motivo.
- Não versionar `db.sqlite3`, `.env` nem ambientes virtuais (já estão no `.gitignore`).
- Conflitos: se o Git indicar conflito em um merge, abra o arquivo, escolha manualmente o trecho correto,
  `git add` e `git commit`.
