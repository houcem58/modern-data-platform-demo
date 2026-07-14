FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt dbt-postgres==1.8.0

COPY . .

LABEL org.opencontainers.image.source="https://github.com/houcem58/modern-data-platform-demo"
LABEL org.opencontainers.image.description="Modern Data Platform — dbt + Airflow + PostgreSQL"
LABEL org.opencontainers.image.licenses="Apache-2.0"

CMD ["python", "ingestion/load_sales.py"]
