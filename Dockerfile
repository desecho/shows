FROM python:3.13-alpine3.23

ENV PROJECT=shows
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .
COPY README.rst .

RUN apk add --no-cache --virtual .build-deps git gcc musl-dev libffi-dev openssl-dev python3-dev cargo && \
    apk add --no-cache mariadb-dev && \
    pip3 install --no-cache-dir uv && \
    uv sync --no-dev --frozen && \
    apk del .build-deps && \
    rm uv.lock pyproject.toml

COPY entrypoint.sh .
COPY src .

EXPOSE 8000

CMD ["./entrypoint.sh"]
