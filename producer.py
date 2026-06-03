from core.mq_client import RabbitMQClient
from core.logger import get_logger

logger = get_logger("geo-producer")

mq = RabbitMQClient(host="localhost")

mq.publish({
    "input_file": "data/sample_geo.json",
    "output_geojson": "outputs/transformed.json",
    "output_csv": "outputs/report.csv",
    "simplify_tolerance": 10
})

logger.info("Job sent to RabbitMQ")