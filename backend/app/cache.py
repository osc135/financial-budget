import os
import json
import redis
from typing import Optional

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))

def get_redis_client() -> Optional[redis.Redis]:
    try:
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        return client
    except Exception:
        return None

def get_dashboard_cache(user_id: int) -> Optional[dict]:
    client = get_redis_client()
    if not client:
        return None
    try:
        key = f"dashboard:{user_id}"
        data = client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception:
        return None

def set_dashboard_cache(user_id: int, data: dict, ttl: int = 60) -> bool:
    client = get_redis_client()
    if not client:
        return False
    try:
        key = f"dashboard:{user_id}"
        client.setex(key, ttl, json.dumps(data))
        return True
    except Exception:
        return False

def invalidate_dashboard_cache(user_id: int) -> bool:
    client = get_redis_client()
    if not client:
        return False
    try:
        key = f"dashboard:{user_id}"
        client.delete(key)
        return True
    except Exception:
        return False
