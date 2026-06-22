import json

from core.logger import get_logger

logger = get_logger("geo-sample-generator")


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

    logger.info("Sample GeoJSON generated -> %s", output_path)
