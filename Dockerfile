FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

LABEL org.opencontainers.image.source="https://github.com/houcem58/modern-data-platform-demo"
LABEL org.opencontainers.image.description="Modern Data Platform — dbt + Airflow + PostgreSQL"
LABEL org.opencontainers.image.licenses="Apache-2.0"

CMD ["python", "ingestion/load_sales.py"]
