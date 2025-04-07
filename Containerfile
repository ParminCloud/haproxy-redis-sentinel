FROM docker.io/python:3.12-slim AS base

ENV DEBIAN_FRONTEND=noninteractive

FROM base AS python-base
ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1 \
	PIP_NO_CACHE_DIR=off \
	PIP_DISABLE_PIP_VERSION_CHECK=on \
	PIP_DEFAULT_TIMEOUT=100 \
	POETRY_HOME="/opt/poetry" \
	POETRY_VIRTUALENVS_IN_PROJECT=true \
	POETRY_NO_INTERACTION=1 \
	PYSETUP_PATH="/opt/pysetup" \
	VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

FROM python-base AS builder-base
RUN apt-get update \
	&& apt-get install --no-install-recommends -y \
	curl \
	build-essential

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR $PYSETUP_PATH
COPY ./poetry.lock ./pyproject.toml ./
RUN poetry install --only main --no-root

FROM python-base AS production

COPY --from=builder-base $VENV_PATH $VENV_PATH

COPY ./haproxy_redis_sentinel /haproxy_redis_sentinel
WORKDIR /haproxy_redis_sentinel

COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/haproxy_redis_sentinel/cli.py"]
