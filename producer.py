from queue import RabbitMQClient

mq = RabbitMQClient(host="localhost")

mq.publish({
    "input_file": "data/sample_geo.json",
    "output_geojson": "outputs/transformed.json",
    "output_csv": "outputs/report.csv",
    "simplify_tolerance": 10
})

print("Job sent")