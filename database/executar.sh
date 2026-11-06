#!/usr/bin/env bash
# Cria o banco "descarte" do zero e executa os cinco scripts, na ordem.
# Uso:  ./executar.sh            (usa o usuário atual do PostgreSQL)
#       PGUSER=postgres ./executar.sh
set -euo pipefail
cd "$(dirname "$0")"
BANCO="${BANCO:-descarte}"
psql -v ON_ERROR_STOP=1 -q -d postgres -c "DROP DATABASE IF EXISTS ${BANCO}" -c "CREATE DATABASE ${BANCO}"
for f in 01_schema.sql 02_dados.sql 03_consultas.sql 04_atualizacao_remocao.sql 05_testes_integridade.sql; do
  echo "================ ${f} ================"
  psql -v ON_ERROR_STOP=1 -q -d "${BANCO}" -f "${f}"
done
