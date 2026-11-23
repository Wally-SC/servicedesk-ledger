.DEFAULT_GOAL := ajuda
.PHONY: ajuda instalar fmt lint tipos teste teste-tudo migrar up down logs psql

ajuda:  ## Lista os alvos disponíveis
	@grep -E '^[a-z-]+:.*?##' $(MAKEFILE_LIST) | sed -e 's/:.*##/ -/'

instalar:  ## Instala as dependências de desenvolvimento
	uv sync --frozen --group dev

fmt:  ## Formata e corrige o que dá para corrigir sozinho
	uv run ruff format src tests
	uv run ruff check --fix src tests

lint:  ## Verifica estilo sem alterar arquivo
	uv run ruff format --check src tests
	uv run ruff check src tests

tipos:  ## Verifica a tipagem
	uv run mypy

teste:  ## Roda os testes que não exigem banco
	uv run pytest -m "not integracao"

teste-tudo:  ## Roda a suíte inteira dentro do compose, contra o banco
	docker compose run --rm app pytest

migrar:  ## Aplica as migrações no banco do compose
	docker compose run --rm app alembic upgrade head

up:  ## Sobe o banco e a aplicação
	@test -f .env || cp .env.example .env
	docker compose up -d --build
	@echo "Saúde: http://localhost:8000/saude"

down:  ## Derruba a stack
	docker compose down

logs:  ## Acompanha os logs da aplicação
	docker compose logs -f app

psql:  ## Abre o psql no banco da aplicação
	docker compose exec db psql -U sdledger -d sdledger
