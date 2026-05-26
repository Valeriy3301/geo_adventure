import json
import math
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer


class GeoDataTransformer:
    """
    Geo-processing application for transforming, cleaning,
    analyzing and exporting GeoJSON datasets.

    Features:
    - CRS transformation
    - Geometry simplification
    - Area / length calculation
    - Bounding box generation
    - Feature filtering
    - Export pipeline
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
        """
        Example:
        source_epsg='EPSG:4326'
        target_epsg='EPSG:3857'
        """

        transformer = Transformer.from_crs(source_epsg, target_epsg, always_xy=True)

        transformed_features = []

        for feature in self.features:
            geometry = shape(feature["geometry"])

            transformed_geometry = transform(transformer.transform, geometry)

            transformed_feature = {
                "type": "Feature",
                "properties": feature.get("properties", {}),
                "geometry": mapping(transformed_geometry),
            }

            transformed_features.append(transformed_feature)

        self.features = transformed_features

        print(f"Transformed CRS: {source_epsg} -> {target_epsg}")

    def simplify_geometries(self, tolerance: float = 0.001):
        simplified_features = []

        for feature in self.features:
            geometry = shape(feature["geometry"])

            simplified_geometry = geometry.simplify(tolerance, preserve_topology=True)

            simplified_feature = {
                "type": "Feature",
                "properties": feature.get("properties", {}),
                "geometry": mapping(simplified_geometry),
            }

            simplified_features.append(simplified_feature)

        self.features = simplified_features

        print(f"Simplified geometries with tolerance={tolerance}")

    def filter_features(self, property_name: str, value: Any):
        filtered = []

        for feature in self.features:
            properties = feature.get("properties", {})

            if properties.get(property_name) == value:
                filtered.append(feature)

        self.features = filtered

        print(f"Filtered dataset -> {len(filtered)} features")

    def enrich_features(self):
        """
        Adds:
        - area
        - perimeter
        - centroid
        - bounding box
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

            enriched_feature = {
                "type": "Feature",
                "properties": properties,
                "geometry": mapping(geometry),
            }

            enriched.append(enriched_feature)

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
        print("---------------------")
        print(f"Valid geometries:   {valid}")
        print(f"Invalid geometries: {invalid}")

    def dataset_statistics(self):
        rows = []

        for feature in self.features:
            geometry = shape(feature["geometry"])

            rows.append(
                {
                    "geometry_type": geometry.geom_type,
                    "area": geometry.area,
                    "length": geometry.length,
                }
            )

        df = pd.DataFrame(rows)

        print("\nDataset Statistics")
        print("------------------")
        print(df.describe(include="all"))

        return df

    def export_geojson(self, output_path: str):
        output = {"type": "FeatureCollection", "features": self.features}

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


class GeoPipeline:
    """
    ETL-style pipeline for geo data engineering.
    """

    def __init__(self, transformer: GeoDataTransformer):
        self.transformer = transformer

    def run(self, input_file: str, output_geojson: str, output_csv: str):
        print("\n=== GEO DATA PIPELINE STARTED ===\n")

        self.transformer.load_geojson(input_file)

        self.transformer.validate_geometries()

        self.transformer.transform_crs("EPSG:4326", "EPSG:3857")

        self.transformer.simplify_geometries(10)

        self.transformer.enrich_features()

        self.transformer.dataset_statistics()

        self.transformer.export_geojson(output_geojson)

        self.transformer.export_csv(output_csv)

        print("\n=== PIPELINE FINISHED ===")


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
    input_file = "sample_geo.json"
    output_geojson = "transformed_geo.json"
    output_csv = "geo_report.csv"

    generate_sample_geojson(input_file)

    transformer = GeoDataTransformer()

    pipeline = GeoPipeline(transformer)

    pipeline.run(
        input_file=input_file, output_geojson=output_geojson, output_csv=output_csv
    )
