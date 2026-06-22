import json
import sys

from core.pipeline import GeoPipeline
from core.sample_data import generate_sample_geojson
from core.transformer import GeoDataTransformer
from infra.rabbitmq_client import RabbitMQConsumer
from infra.redis_client import RedisCache


def create_pipeline():
    cache = RedisCache()
    transformer = GeoDataTransformer()

    return GeoPipeline(transformer=transformer, cache=cache)


def worker_callback(ch, method, properties, body):
    job = json.loads(body)

    pipeline = create_pipeline()

    try:
        pipeline.run(job)

    except Exception as e:
        print(f"Job failed: {e}")


def run_worker():
    consumer = RabbitMQConsumer()
    consumer.consume(worker_callback)


def run_local():
    input_file = "data/sample_geo.json"

    output_geojson = "outputs/transformed_geo.json"

    output_csv = "outputs/geo_report.csv"

    generate_sample_geojson(input_file)

    pipeline = create_pipeline()

    pipeline.run(
        {
            "input_file": input_file,
            "output_geojson": output_geojson,
            "output_csv": output_csv,
            "simplify_tolerance": 10,
        }
    )


if __name__ == "__main__":

    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        run_worker()

    else:
        run_local()
