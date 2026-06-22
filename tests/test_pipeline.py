from core.pipeline import GeoPipeline
from core.transformer import GeoDataTransformer


class FakeCache:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value


def test_pipeline_runs(tmp_path):
    input_file = tmp_path / "input.json"
    output_geojson = tmp_path / "out.json"
    output_csv = tmp_path / "out.csv"

    # minimal geo sample
    input_file.write_text(
        """
    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "properties": {"name": "A"},
          "geometry": {
            "type": "Polygon",
            "coordinates": [[[0,0],[1,0],[1,1],[0,1],[0,0]]]
          }
        }
      ]
    }
    """
    )

    pipeline = GeoPipeline(transformer=GeoDataTransformer(), cache=FakeCache())

    result = pipeline.run(
        {
            "input_file": str(input_file),
            "output_geojson": str(output_geojson),
            "output_csv": str(output_csv),
            "simplify_tolerance": 1,
        }
    )

    assert result["status"] == "completed"
    assert output_geojson.exists()
    assert output_csv.exists()
