FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local \
    UV_COMPILE_BYTECODE=1

# Mesma versão do uv que gerou o uv.lock, para o --frozen não divergir.
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv

WORKDIR /app

# As dependências entram antes do código: trocar uma linha de src não invalida
# a camada de instalação.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --group dev

COPY src ./src
COPY tests ./tests
RUN uv sync --frozen --group dev

EXPOSE 8000
CMD ["uvicorn", "sdledger.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
