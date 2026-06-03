from typing import Dict, Any

from core.clustering import GeoClusterer

from core.logger import get_logger


class GeoPipeline:
    """
    ETL-style orchestration layer.
    """

    def __init__(self, transformer, cache=None):
        self.transformer = transformer
        self.cache = cache
        self.logger = get_logger("geo-pipeline")

    def run(self, job: Dict[str, Any]):
        input_file = job["input_file"]
        output_geojson = job["output_geojson"]
        output_csv = job["output_csv"]

        simplify_tolerance = job.get("simplify_tolerance", 10)

        crs_source = job.get("crs_source", "EPSG:4326")
        crs_target = job.get("crs_target", "EPSG:3857")

        enable_enrichment = job.get("enable_enrichment", True)
        enable_clustering = job.get("enable_clustering", False)
        enable_stats = job.get("enable_stats", False)

        cluster_eps = job.get("cluster_eps", 0.01)
        cluster_min_samples = job.get("cluster_min_samples", 2)

        # improved cache key (includes key pipeline params)
        cache_key = (
            f"geo:{input_file}:"
            f"{simplify_tolerance}:"
            f"{crs_source}->{crs_target}:"
            f"cluster={enable_clustering}"
        )

        if self.cache:
            cached = self.cache.get(cache_key)

            if cached:
                self.logger.info("CACHE HIT -> skipping processing")
                return cached

        self.logger.info("\n=== GEO PIPELINE STARTED ===\n")

        self.transformer.load_geojson(input_file)

        self.transformer.validate_geometries()

        self.transformer.transform_crs(
            crs_source,
            crs_target
        )

        self.transformer.simplify_geometries(
            simplify_tolerance
        )

        if enable_enrichment:
            self.transformer.enrich_features()

        if enable_clustering:
            clusterer = GeoClusterer(
                eps=cluster_eps,
                min_samples=cluster_min_samples
            )

            self.transformer.features = clusterer.cluster(
                self.transformer.features
            )

            self.logger.info("Clustering completed")

        if enable_stats:
            self.transformer.dataset_statistics()

        self.transformer.export_geojson(output_geojson)
        self.transformer.export_csv(output_csv)

        result = {
            "status": "completed",
            "input_file": input_file,
            "output_geojson": output_geojson,
            "output_csv": output_csv,
            "crs": {
                "source": crs_source,
                "target": crs_target
            },
            "clustering_enabled": enable_clustering,
        }

        if self.cache:
            self.cache.set(cache_key, result)

        self.logger.info("\n=== GEO PIPELINE FINISHED ===\n")

        return result