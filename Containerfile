FROM docker.io/library/python:3.12

ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN pip3 install poetry

WORKDIR /app

COPY . /app/

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

ENTRYPOINT [ "poetry", "run", "haproxy-redis-sentinel" ]
