# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Dépendances système : compilation, PostgreSQL, Graphviz (diagrammes normes)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        graphviz \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Fichiers statiques collectés dans l'image (WhiteNoise les sert ensuite)
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# ASGI via Daphne : HTTP + WebSockets (channels) dans un seul process.
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
