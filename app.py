import json
import math
import redis
import pika

import pandas as pd

from pathlib import Path
from typing import Dict, List, Any

from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer




class RedisCache:
    def __init__(self, host="localhost", port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def get(self, key):
        val = self.client.get(key)
        return json.loads(val) if val else None

    def set(self, key, value, ttl=3600):
        self.client.set(key, json.dumps(value), ex=ttl)


class RabbitMQConsumer:
    def __init__(self, host="localhost", queue="geo_jobs"):
        self.queue = queue

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))

        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue)

    def consume(self, callback):
        self.channel.basic_consume(
            queue=self.queue, on_message_callback=callback, auto_ack=True
        )
        print("Waiting for geo jobs...")
        self.channel.start_consuming()


class GeoDataTransformer:
    """
    Geo-processing application for transforming, cleaning,
    analyzing and exporting GeoJSON datasets.
    """

    def __init__(self):
        self.data = None
        self.features = []

    def load_geojson(self, filepath: str):
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        if self.data.get("type") != "FeatureCollection":
            raise ValueError("GeoJSON must be a FeatureCollection")

        self.features = self.data.get("features", [])

        print(f"Loaded {len(self.features)} features")

    def transform_crs(self, source_epsg: str, target_epsg: str):
        transformer = Transformer.from_crs(source_epsg, target_epsg, always_xy=True)

        transformed_features = []

        for feature in self.features:
            geometry = shape(feature["geometry"])
            transformed_geometry = transform(transformer.transform, geometry)

            transformed_features.append(
                {
                    "type": "Feature",
                    "properties": feature.get("properties", {}),
                    "geometry": mapping(transformed_geometry),
                }
            )

        self.features = transformed_features
        print(f"Transformed CRS: {source_epsg} -> {target_epsg}")

    def simplify_geometries(self, tolerance: float = 0.001):
        simplified = []

        for feature in self.features:
            geometry = shape(feature["geometry"])
            simplified_geom = geometry.simplify(tolerance, preserve_topology=True)

            simplified.append(
                {
                    "type": "Feature",
                    "properties": feature.get("properties", {}),
                    "geometry": mapping(simplified_geom),
                }
            )

        self.features = simplified
        print(f"Simplified geometries with tolerance={tolerance}")

    def enrich_features(self):
        enriched = []

        for feature in self.features:
            geometry = shape(feature["geometry"])
            props = feature.get("properties", {}).copy()

            props["area"] = geometry.area
            props["perimeter"] = geometry.length
            props["bbox"] = geometry.bounds
            props["centroid_x"] = geometry.centroid.x
            props["centroid_y"] = geometry.centroid.y

            enriched.append(
                {
                    "type": "Feature",
                    "properties": props,
                    "geometry": mapping(geometry),
                }
            )

        self.features = enriched
        print("Feature enrichment completed")

    def export_geojson(self, output_path: str):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {"type": "FeatureCollection", "features": self.features}, f, indent=2
            )

        print(f"GeoJSON exported -> {output_path}")

    def export_csv(self, output_path: str):
        rows = []

        for feature in self.features:
            row = feature.get("properties", {}).copy()
            geometry = shape(feature["geometry"])
            row["geometry_type"] = geometry.geom_type
            rows.append(row)

        pd.DataFrame(rows).to_csv(output_path, index=False)
        print(f"CSV exported -> {output_path}")


class GeoPipeline:
    def __init__(self, transformer: GeoDataTransformer, cache: RedisCache = None):
        self.transformer = transformer
        self.cache = cache

    def run(self, job: Dict[str, Any]):
        input_file = job["input_file"]
        output_geojson = job["output_geojson"]
        output_csv = job["output_csv"]

        cache_key = f"geo:job:{input_file}"

        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                print("CACHE HIT -> skipping processing")
                return cached

        print("\n=== PIPELINE START ===\n")

        self.transformer.load_geojson(input_file)
        self.transformer.transform_crs("EPSG:4326", "EPSG:3857")
        self.transformer.simplify_geometries(job.get("simplify_tolerance", 10))
        self.transformer.enrich_features()

        self.transformer.export_geojson(output_geojson)
        self.transformer.export_csv(output_csv)

        result = {"status": "completed", "input": input_file}

        if self.cache:
            self.cache.set(cache_key, result)

        print("\n=== PIPELINE FINISHED ===")
        return result


def create_worker():
    cache = RedisCache()
    transformer = GeoDataTransformer()
    pipeline = GeoPipeline(transformer, cache=cache)

    def callback(ch, method, properties, body):
        job = json.loads(body)
        print(f"Received job: {job}")

        try:
            pipeline.run(job)
        except Exception as e:
            print(f"Job failed: {e}")

    return callback


def generate_sample_geojson(output_path: str):
    sample = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Region A", "category": "urban"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [16.37, 48.20],
                            [16.38, 48.20],
                            [16.38, 48.21],
                            [16.37, 48.21],
                            [16.37, 48.20],
                        ]
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {"name": "Region B", "category": "industrial"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [16.39, 48.22],
                            [16.40, 48.22],
                            [16.40, 48.23],
                            [16.39, 48.23],
                            [16.39, 48.22],
                        ]
                    ],
                },
            },
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sample, f, indent=2)

    print(f"Sample GeoJSON generated -> {output_path}")


if __name__ == "__main__":

    import sys

    # MODE 1: worker mode (RabbitMQ)
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        consumer = RabbitMQConsumer()
        consumer.consume(create_worker())

    # MODE 2: local CLI pipeline mode
    else:
        input_file = "sample_geo.json"
        output_geojson = "transformed_geo.json"
        output_csv = "geo_report.csv"

        generate_sample_geojson(input_file)

        pipeline = GeoPipeline(GeoDataTransformer())

        pipeline.run(
            {
                "input_file": input_file,
                "output_geojson": output_geojson,
                "output_csv": output_csv,
                "simplify_tolerance": 10,
            }
        )
