import redis
import json


class RedisClient:
    def __init__(self, host="localhost", port=6379, db=0):
        self.r = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )

    def get(self, key):
        val = self.r.get(key)
        return json.loads(val) if val else None

    def set(self, key, value, ttl=3600):
        self.r.set(key, json.dumps(value), ex=ttl)

    def exists(self, key):
        return self.r.exists(key)