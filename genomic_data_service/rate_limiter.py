"""Token-bucket rate limiting for outbound requests to the ENCODE portal.

The indexer (``region_indexer.py``) and the Celery workers (``strand.py``) both
make requests to ``www.encodeproject.org``. To avoid being a "noisy neighbor"
they share a single, approximate requests-per-second budget.

Two backends are provided:

* :class:`_RedisTokenBucket` -- a distributed token bucket whose state lives in
  Redis so that the main process and every Celery worker draw from one shared
  budget. Refill and consume happen atomically inside a Lua script, using the
  Redis server clock so client clock skew does not matter.
* :class:`_InProcessTokenBucket` -- a thread-safe in-process fallback used when
  no Redis URL is configured or Redis is unreachable.

Use :func:`get_portal_limiter` to build the appropriate limiter. All limiters
expose ``acquire(tokens=1)`` which blocks until a token is available.
"""

import math
import random
import threading
import time
import logging

logger = logging.getLogger(__name__)

DEFAULT_PORTAL_LIMITER_KEY = 'gds:portal_ratelimit'


class _NoopLimiter:
    """A limiter that never blocks (used when rate limiting is disabled)."""

    def acquire(self, tokens=1):
        return


class _InProcessTokenBucket:
    """Thread-safe token bucket local to a single process."""

    def __init__(self, rate, capacity):
        self.rate = float(rate)
        self.capacity = float(capacity)
        self._tokens = float(capacity)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens=1):
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._last
                self._last = now
                self._tokens = min(
                    self.capacity, self._tokens + elapsed * self.rate
                )
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                sleep_for = (tokens - self._tokens) / self.rate
            time.sleep(sleep_for)


# Atomically refill and consume a token bucket stored in a Redis hash.
# Uses the Redis server clock (TIME) so client clock skew is irrelevant.
# Returns {allowed, wait_seconds_as_string}.
_REDIS_LUA = """
local key = KEYS[1]
local rate = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local requested = tonumber(ARGV[3])

local t = redis.call('TIME')
local now = tonumber(t[1]) + tonumber(t[2]) / 1000000

local data = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(data[1])
local ts = tonumber(data[2])
if tokens == nil then
    tokens = capacity
    ts = now
end

local elapsed = now - ts
if elapsed < 0 then elapsed = 0 end
tokens = math.min(capacity, tokens + elapsed * rate)

local allowed = 0
local wait = 0
if tokens >= requested then
    tokens = tokens - requested
    allowed = 1
else
    wait = (requested - tokens) / rate
end

redis.call('HSET', key, 'tokens', tokens, 'ts', now)
-- expire idle keys so they don't linger forever
redis.call('PEXPIRE', key, math.ceil((capacity / rate) * 1000) + 1000)

return {allowed, tostring(wait)}
"""


class _RedisTokenBucket:
    """Distributed token bucket shared across processes via Redis."""

    def __init__(self, redis_client, key, rate, capacity):
        self.redis = redis_client
        self.key = key
        self.rate = float(rate)
        self.capacity = float(capacity)
        self._script = redis_client.register_script(_REDIS_LUA)

    def acquire(self, tokens=1):
        while True:
            try:
                allowed, wait = self._script(
                    keys=[self.key],
                    args=[self.rate, self.capacity, tokens],
                )
            except Exception as e:
                # Never let a Redis hiccup block indexing; degrade to no limit.
                logger.warning(
                    'Portal rate limiter: Redis error (%s); allowing request.',
                    e,
                )
                return

            if int(allowed) == 1:
                return

            if isinstance(wait, bytes):
                wait = wait.decode()
            wait = float(wait)
            # Small jitter avoids many waiters waking simultaneously.
            time.sleep(max(wait, 0.005) + random.uniform(0, 0.01))


def get_portal_limiter(
    rps, redis_url=None, burst=None, key=DEFAULT_PORTAL_LIMITER_KEY
):
    """Build a limiter capping requests at approximately ``rps`` per second.

    ``rps`` <= 0 (or ``None``) disables rate limiting. When ``redis_url`` is
    provided and reachable, a shared Redis-backed bucket is returned; otherwise
    an in-process bucket is used. ``burst`` sets the bucket capacity (max
    instantaneous burst); it defaults to ``ceil(rps)``.
    """
    if not rps or rps <= 0:
        return _NoopLimiter()

    capacity = float(burst) if burst else max(1.0, math.ceil(rps))

    if redis_url:
        try:
            import redis

            client = redis.Redis.from_url(
                redis_url, socket_connect_timeout=1, socket_timeout=1
            )
            client.ping()
            logger.info(
                'Portal rate limiter: using shared Redis bucket at %.3g req/s '
                '(burst %.3g).', rps, capacity
            )
            return _RedisTokenBucket(client, key, rps, capacity)
        except Exception as e:
            logger.warning(
                'Portal rate limiter: Redis unavailable (%s); falling back to '
                'in-process limiter.', e
            )

    logger.info(
        'Portal rate limiter: using in-process bucket at %.3g req/s '
        '(burst %.3g).', rps, capacity
    )
    return _InProcessTokenBucket(rps, capacity)
