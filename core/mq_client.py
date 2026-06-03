import json
import pika


class RabbitMQClient:
    def __init__(self, host="localhost", queue_name="geo_jobs"):
        self.host = host
        self.queue_name = queue_name

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host)
        )

        self.channel = self.connection.channel()

        self.channel.queue_declare(queue=self.queue_name, durable=True)

    def publish(self, message: dict):
        body = json.dumps(message)

        self.channel.basic_publish(
            exchange="",
            routing_key=self.queue_name,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2
            ),
        )

    def close(self):
        self.connection.close()