FROM python:3.10-slim as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /app

FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.4.1

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./

COPY AirbnbScraper ./AirbnbScraper

RUN poetry config virtualenvs.in-project true && \
    poetry install --only=main --no-root && \
    poetry build

FROM base as runner

COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/dist .
COPY caller.py entrypoint.sh ./

RUN ./.venv/bin/pip install *.whl
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

