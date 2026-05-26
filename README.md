# Geo Data Transformer

Geo Data Transformer is a Python-based geo-processing system that supports both:

- Local ETL execution (CLI mode)
- Distributed asynchronous processing (RabbitMQ + Redis worker mode)

This project supports a hybrid execution model:

### 1. Local Mode (Development / Testing)
- Runs pipeline sequentially in a single process
- No external services required

### 2. Distributed Mode (Production)
- RabbitMQ handles job queuing
- Redis handles caching + idempotency
- Worker processes consume geo-processing jobs asynchronously

## Run Locally (CLI Mode)

pip install -r requirements.txt
python app.py

## Run Distributed System (Worker Mode)

### Start infrastructure
docker-compose up -d

### Start worker
python app.py worker

## Submit Jobs (RabbitMQ)

Jobs are submitted in JSON format:

{
  "input_file": "data/sample_geo.json",
  "output_geojson": "outputs/out.json",
  "output_csv": "outputs/out.csv",
  "simplify_tolerance": 10
}

## Infrastructure Requirements (Distributed Mode)

- Redis (caching + state management)
- RabbitMQ (job queue)

These can be started using Docker Compose.