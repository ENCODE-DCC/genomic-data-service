"""Rate limiting for outbound requests to the ENCODE portal.

The indexer (``region_indexer.py``) and the Celery workers (``strand.py``) both
make requests to ``www.encodeproject.org``. To avoid being a "noisy neighbor"
they share a single, approximate requests-per-second budget.

Two backends are provided:

* :class:`_RedisFixedWindow` -- a distributed limiter whose state lives in Redis
  so the main process and every Celery worker share one budget. It uses a
  per-second counter (``INCR`` on a ``key:<epoch_second>`` key, which is atomic
  on its own -- no Lua needed). A fixed window can admit up to ~2x the rate
  across a window boundary; that is acceptable for an approximate throttle.
* :class:`_InProcessTokenBucket` -- a thread-safe in-process fallback used when
  no Redis URL is configured or Redis is unreachable.

Use :func:`get_portal_limiter` to build the appropriate limiter. All limiters
expose ``acquire(tokens=1)`` which blocks until a request may proceed.
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


class _RedisFixedWindow:
    """Distributed fixed-window rate limiter shared across processes via Redis.

    One counter per clock-second: ``INCR`` is atomic, so no read-modify-write
    coordination (or Lua) is required. When a second's counter exceeds the
    budget, callers wait until the next second and try again.
    """

    def __init__(self, redis_client, key, rps):
        self.redis = redis_client
        self.key = key
        # Whole requests per one-second window.
        self.rps = max(1, int(math.ceil(rps)))

    def acquire(self, tokens=1):
        while True:
            now = time.time()
            window = int(now)
            window_key = f'{self.key}:{window}'
            try:
                count = self.redis.incr(window_key)
                if count == 1:
                    # Expire a little past the window so keys clean themselves up.
                    self.redis.expire(window_key, 2)
            except Exception as e:
                # Never let a Redis hiccup block indexing; degrade to no limit.
                logger.warning(
                    'Portal rate limiter: Redis error (%s); allowing request.',
                    e,
                )
                return

            if count <= self.rps:
                return

            # Over budget for this second: wait out the rest of it (plus jitter
            # so many waiters don't all wake on the exact boundary).
            time.sleep(max(0.0, window + 1 - now) + random.uniform(0, 0.05))


def get_portal_limiter(
    rps, redis_url=None, burst=None, key=DEFAULT_PORTAL_LIMITER_KEY
):
    """Build a limiter capping requests at approximately ``rps`` per second.

    ``rps`` <= 0 (or ``None``) disables rate limiting. When ``redis_url`` is
    provided and reachable, a shared Redis-backed limiter is returned; otherwise
    an in-process token bucket is used. ``burst`` sets the in-process bucket
    capacity (max instantaneous burst) and defaults to ``ceil(rps)``; it has no
    effect on the Redis fixed-window backend.
    """
    if not rps or rps <= 0:
        return _NoopLimiter()

    if redis_url:
        try:
            import redis

            client = redis.Redis.from_url(
                redis_url, socket_connect_timeout=1, socket_timeout=1
            )
            client.ping()
            logger.info(
                'Portal rate limiter: using shared Redis window at %.3g req/s.',
                rps,
            )
            return _RedisFixedWindow(client, key, rps)
        except Exception as e:
            logger.warning(
                'Portal rate limiter: Redis unavailable (%s); falling back to '
                'in-process limiter.', e
            )

    capacity = float(burst) if burst else max(1.0, math.ceil(rps))
    logger.info(
        'Portal rate limiter: using in-process bucket at %.3g req/s '
        '(burst %.3g).', rps, capacity
    )
    return _InProcessTokenBucket(rps, capacity)
