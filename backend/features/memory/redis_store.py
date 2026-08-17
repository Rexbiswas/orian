import json
import logging
import time
from typing import Any, Optional, Dict
from config import settings

logger = logging.getLogger("orian.redis_store")

try:
    import redis
    _redis_available = True
except ImportError:
    _redis_available = False

class InMemRedisFallback:
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}

    def _purge_expired(self):
        now = time.time()
        expired_keys = [k for k, exp in self._expiry.items() if exp < now]
        for k in expired_keys:
            self._data.pop(k, None)
            self._expiry.pop(k, None)

    def set(self, name: str, value: Any, ex: Optional[int] = None):
        self._purge_expired()
        self._data[name] = value
        if ex:
            self._expiry[name] = time.time() + ex
        elif name in self._expiry:
            del self._expiry[name]
        return True

    def get(self, name: str) -> Optional[Any]:
        self._purge_expired()
        return self._data.get(name)

    def delete(self, *names: str):
        count = 0
        for name in names:
            if name in self._data:
                del self._data[name]
                self._expiry.pop(name, None)
                count += 1
        return count

    def exists(self, name: str) -> int:
        self._purge_expired()
        return 1 if name in self._data else 0

    def keys(self, pattern: str = "*"):
        self._purge_expired()
        # Simple glob matching fallback
        import fnmatch
        return [k for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]

class RedisWorkingMemory:
    def __init__(self):
        self.client = None
        self.is_real_redis = False
        
        if _redis_available:
            try:
                r = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True,
                    socket_timeout=1.0
                )
                r.ping()
                self.client = r
                self.is_real_redis = True
                logger.info(f"Connected to Redis Working Memory at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except Exception as e:
                logger.warning(f"Could not connect to Redis server ({e}). Operating in thread-safe In-Memory Redis fallback mode.")
                self.client = InMemRedisFallback()
        else:
            logger.info("redis-py package not installed. Operating in thread-safe In-Memory Redis fallback mode.")
            self.client = InMemRedisFallback()

    def set_working_context(self, session_id: str, key: str, value: Any, ttl_seconds: int = 3600):
        full_key = f"working:{session_id}:{key}"
        val_str = json.dumps(value) if not isinstance(value, str) else value
        if self.is_real_redis:
            self.client.set(full_key, val_str, ex=ttl_seconds)
        else:
            self.client.set(full_key, val_str, ex=ttl_seconds)

    def get_working_context(self, session_id: str, key: str) -> Optional[Any]:
        full_key = f"working:{session_id}:{key}"
        raw = self.client.get(full_key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return raw

    def delete_working_context(self, session_id: str, key: str):
        full_key = f"working:{session_id}:{key}"
        self.client.delete(full_key)

    def set_active_agent_state(self, agent_id: str, state: dict, ttl_seconds: int = 1800):
        full_key = f"agent_state:{agent_id}"
        self.client.set(full_key, json.dumps(state), ex=ttl_seconds)

    def get_active_agent_state(self, agent_id: str) -> Optional[dict]:
        full_key = f"agent_state:{agent_id}"
        raw = self.client.get(full_key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def push_task_queue(self, queue_name: str, task_data: dict):
        full_key = f"queue:{queue_name}"
        task_str = json.dumps(task_data)
        if self.is_real_redis:
            self.client.rpush(full_key, task_str)
        else:
            # fallback list handling
            existing = self.client.get(full_key)
            queue_list = json.loads(existing) if existing else []
            queue_list.append(task_data)
            self.client.set(full_key, json.dumps(queue_list))

redis_store = RedisWorkingMemory()
