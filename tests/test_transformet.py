import json
import os

from core.sample_data import generate_sample_geojson
from core.transformer import GeoDataTransformer


def test_load_geojson(tmp_path):
    file_path = tmp_path / "sample.json"

    generate_sample_geojson(file_path)

    transformer = GeoDataTransformer()
    transformer.load_geojson(str(file_path))

    assert transformer.features is not None
    assert len(transformer.features) == 2


def test_transform_crs(tmp_path):
    file_path = tmp_path / "sample.json"

    generate_sample_geojson(file_path)

    transformer = GeoDataTransformer()
    transformer.load_geojson(str(file_path))

    transformer.transform_crs("EPSG:4326", "EPSG:3857")

    assert len(transformer.features) == 2


def test_enrich_features(tmp_path):
    file_path = tmp_path / "sample.json"

    generate_sample_geojson(file_path)

    transformer = GeoDataTransformer()
    transformer.load_geojson(str(file_path))

    transformer.enrich_features()

    feature = transformer.features[0]

    assert "area" in feature["properties"]
    assert "centroid_x" in feature["properties"]
