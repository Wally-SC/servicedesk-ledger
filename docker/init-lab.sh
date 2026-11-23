#!/bin/sh
# Cria o banco do laboratório de índices ao lado do banco da aplicação.
# Uma instância, dois bancos: o DDL do laboratório nunca toca os dados da
# aplicação, e a stack continua leve (decisão D12).
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
CREATE DATABASE "${LAB_POSTGRES_DB}" OWNER "${POSTGRES_USER}";
SQL
