FROM ghcr.io/astral-sh/uv:0.13.6 AS uv
FROM python:3.14-slim

COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project --no-cache
COPY src ./src
RUN uv sync --locked --no-dev --no-editable --no-cache

EXPOSE 18080
CMD ["uvicorn", "ezdocker.api:app", "--host", "0.0.0.0", "--port", "18080"]
