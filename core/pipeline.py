from typing import Dict, Any


class GeoPipeline:
    """
    ETL-style orchestration layer.
    """

    def __init__(self, transformer, cache=None):
        self.transformer = transformer
        self.cache = cache

    def run(self, job: Dict[str, Any]):
        input_file = job["input_file"]

        output_geojson = job["output_geojson"]

        output_csv = job["output_csv"]

        simplify_tolerance = job.get(
            "simplify_tolerance",
            10
        )

        cache_key = f"geo:{input_file}"

        # Cache check
        if self.cache:
            cached = self.cache.get(cache_key)

            if cached:
                print("CACHE HIT -> skipping processing")
                return cached

        print("\n=== GEO PIPELINE STARTED ===\n")

        self.transformer.load_geojson(input_file)

        self.transformer.validate_geometries()

        self.transformer.transform_crs(
            "EPSG:4326",
            "EPSG:3857"
        )

        self.transformer.simplify_geometries(
            simplify_tolerance
        )

        self.transformer.enrich_features()

        self.transformer.dataset_statistics()

        self.transformer.export_geojson(
            output_geojson
        )

        self.transformer.export_csv(
            output_csv
        )

        result = {
            "status": "completed",
            "input_file": input_file,
            "output_geojson": output_geojson,
            "output_csv": output_csv,
        }

        # Store pipeline result
        if self.cache:
            self.cache.set(cache_key, result)

        print("\n=== GEO PIPELINE FINISHED ===")

        return result