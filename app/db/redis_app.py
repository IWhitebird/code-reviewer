import os
import logging
import redis
from dotenv import load_dotenv

load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

def create_redis_client(host: str = REDIS_HOST, port: int = REDIS_PORT , db : int = REDIS_DB) -> redis.Redis:
    client = redis.Redis(host=host, port=port ,db=db)
    logging.info(f"Connected to Redis at {host}:{port}")
    return client

redis_app = create_redis_client()
