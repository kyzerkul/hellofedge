# Image unique de Hellofedge : elle sert l'api, le worker et l'étape de migration.

# Étape 1 : construire le cockpit (Node sert seulement ici, jamais en production).
FROM node:22.23.3-slim AS cockpit
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Étape 2 : l'image finale Python.
FROM python:3.13.15-slim
COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1
WORKDIR /app/backend

# Dépendances d'abord (couche mise en cache), puis le code.
COPY backend/pyproject.toml backend/uv.lock backend/.python-version ./
RUN uv sync --locked --no-dev --no-install-project
COPY backend/ ./
RUN uv sync --locked --no-dev

COPY --from=cockpit /app/frontend/dist /app/frontend/dist

ENV PATH="/app/backend/.venv/bin:$PATH" \
    FRONTEND_DIST=/app/frontend/dist

RUN useradd --system --uid 1000 hellofedge
USER hellofedge

EXPOSE 8000
# Par défaut : l'api. Le worker et la migration changent la commande dans docker-compose.yml.
CMD ["uvicorn", "hellofedge.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
