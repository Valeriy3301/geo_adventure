import os
from core.sample_data import generate_sample_geojson


def test_sample_geojson(tmp_path):
    file_path = tmp_path / "sample.json"

    generate_sample_geojson(file_path)

    assert file_path.exists()

    data = file_path.read_text()
    assert "FeatureCollection" in data
    assert "Region A" in data