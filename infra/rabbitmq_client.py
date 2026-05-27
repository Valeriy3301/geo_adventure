import pika
import json


class RabbitMQClient:
    def __init__(self, host="localhost", queue="geo_jobs"):
        self.queue = queue

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host)
        )

        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue)

    def publish(self, job: dict):
        self.channel.basic_publish(
            exchange="",
            routing_key=self.queue,
            body=json.dumps(job)
        )

    def consume(self, callback):
        self.channel.basic_consume(
            queue=self.queue,
            on_message_callback=callback,
            auto_ack=True
        )

        print("Waiting for jobs...")
        self.channel.start_consuming()