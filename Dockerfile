FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry
COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false

COPY . .
RUN poetry install --without dev --no-interaction --no-ansi --no-root

RUN useradd -m -u 1000 webuser && chown -R webuser:webuser /app
USER webuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "image_gallery.main:create_app()"]
