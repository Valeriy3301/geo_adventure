import json
from pathlib import Path
from typing import Any

import pandas as pd
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer

from core.logger import get_logger


class GeoDataTransformer:
    """
    Core geo-processing engine.

    Features:
    - CRS transformation
    - Geometry simplification
    - Feature enrichment
    - Statistics generation
    - Export utilities
    """

    def __init__(self):
        self.data = None
        self.features = []
        self.logger = get_logger("geo-transformer")

    def load_geojson(self, filepath: str):
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        if self.data.get("type") != "FeatureCollection":
            raise ValueError("GeoJSON must be a FeatureCollection")

        self.features = self.data.get("features", [])

        self.logger.info("Loaded %s features", len(self.features))

    def transform_crs(self, source_epsg: str, target_epsg: str):
        transformer = Transformer.from_crs(
            source_epsg,
            target_epsg,
            always_xy=True
        )

        transformed = []

        for feature in self.features:
            geometry = shape(feature["geometry"])

            transformed_geometry = transform(
                transformer.transform,
                geometry
            )

            transformed.append({
                "type": "Feature",
                "properties": feature.get("properties", {}),
                "geometry": mapping(transformed_geometry),
            })

        self.features = transformed

        self.logger.info("CRS transformed: %s -> %s", source_epsg, target_epsg)

    def simplify_geometries(self, tolerance: float = 0.001):
        simplified = []

        for feature in self.features:
            geometry = shape(feature["geometry"])

            simplified_geometry = geometry.simplify(
                tolerance,
                preserve_topology=True
            )

            simplified.append({
                "type": "Feature",
                "properties": feature.get("properties", {}),
                "geometry": mapping(simplified_geometry),
            })

        self.features = simplified

        self.logger.info("Geometries simplified (tolerance=%s)", tolerance)

    def filter_features(self, property_name: str, value: Any):
        filtered = []

        for feature in self.features:
            properties = feature.get("properties", {})

            if properties.get(property_name) == value:
                filtered.append(feature)

        self.features = filtered

        self.logger.info("Filtered features count: %s", len(filtered))

    def enrich_features(self):
        """
        Adds:
        - area
        - perimeter
        - centroid
        - bbox
        """

        enriched = []

        for feature in self.features:
            geometry = shape(feature["geometry"])

            properties = feature.get("properties", {}).copy()

            properties["area"] = geometry.area
            properties["perimeter"] = geometry.length
            properties["bbox"] = geometry.bounds
            properties["centroid_x"] = geometry.centroid.x
            properties["centroid_y"] = geometry.centroid.y

            enriched.append({
                "type": "Feature",
                "properties": properties,
                "geometry": mapping(geometry),
            })

        self.features = enriched

        self.logger.info("Feature enrichment completed")

    def validate_geometries(self):
        valid = 0
        invalid = 0

        for feature in self.features:
            geometry = shape(feature["geometry"])

            if geometry.is_valid:
                valid += 1
            else:
                invalid += 1

        self.logger.info("Geometry validation completed")
        self.logger.info("Valid: %s | Invalid: %s", valid, invalid)

    def dataset_statistics(self):
        rows = []

        for feature in self.features:
            geometry = shape(feature["geometry"])

            rows.append({
                "geometry_type": geometry.geom_type,
                "area": geometry.area,
                "length": geometry.length,
            })

        df = pd.DataFrame(rows)

        self.logger.info("Dataset statistics generated")
        self.logger.info("\n%s", df.describe(include="all"))

        return df

    def export_geojson(self, output_path: str):
        output = {
            "type": "FeatureCollection",
            "features": self.features
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        self.logger.info("GeoJSON exported -> %s", output_path)

    def export_csv(self, output_path: str):
        rows = []

        for feature in self.features:
            row = feature.get("properties", {}).copy()

            geometry = shape(feature["geometry"])
            row["geometry_type"] = geometry.geom_type

            rows.append(row)

        df = pd.DataFrame(rows)

        df.to_csv(output_path, index=False)

        self.logger.info("CSV exported -> %s", output_path)