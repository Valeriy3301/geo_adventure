import json
from pathlib import Path
from typing import Any

import pandas as pd
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer


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

        print(f"CRS transformed: {source_epsg} -> {target_epsg}")

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

        print(f"Geometries simplified (tolerance={tolerance})")

    def filter_features(self, property_name: str, value: Any):
        filtered = []

        for feature in self.features:
            properties = feature.get("properties", {})

            if properties.get(property_name) == value:
                filtered.append(feature)

        self.features = filtered

        print(f"Filtered features count: {len(filtered)}")

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

        print("Feature enrichment completed")

    def validate_geometries(self):
        valid = 0
        invalid = 0

        for feature in self.features:
            geometry = shape(feature["geometry"])

            if geometry.is_valid:
                valid += 1
            else:
                invalid += 1

        print("\nGeometry Validation")
        print("-------------------")
        print(f"Valid geometries:   {valid}")
        print(f"Invalid geometries: {invalid}")

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

        print("\nDataset Statistics")
        print("------------------")
        print(df.describe(include="all"))

        return df

    def export_geojson(self, output_path: str):
        output = {
            "type": "FeatureCollection",
            "features": self.features
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        print(f"GeoJSON exported -> {output_path}")

    def export_csv(self, output_path: str):
        rows = []

        for feature in self.features:
            row = feature.get("properties", {}).copy()

            geometry = shape(feature["geometry"])

            row["geometry_type"] = geometry.geom_type

            rows.append(row)

        df = pd.DataFrame(rows)

        df.to_csv(output_path, index=False)

        print(f"CSV exported -> {output_path}")