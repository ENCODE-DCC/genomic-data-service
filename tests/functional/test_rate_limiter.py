import time

import pytest

from genomic_data_service.rate_limiter import (
    _InProcessTokenBucket,
    _NoopLimiter,
    get_portal_limiter,
)


def test_in_process_bucket_allows_burst_up_to_capacity():
    bucket = _InProcessTokenBucket(rate=1000, capacity=5)
    start = time.monotonic()
    for _ in range(5):
        bucket.acquire()
    # A full bucket should let the initial burst through without blocking.
    assert time.monotonic() - start < 0.05


def test_in_process_bucket_throttles_beyond_capacity():
    # 20 tokens/sec, capacity 1 -> each token past the first costs ~0.05s.
    bucket = _InProcessTokenBucket(rate=20, capacity=1)
    bucket.acquire()  # drain the single available token
    start = time.monotonic()
    bucket.acquire()  # must wait for a refill
    assert time.monotonic() - start >= 0.03


def test_in_process_bucket_average_rate():
    # 50/sec, no burst: 5 sequential acquires should take ~4 refills (~0.08s).
    bucket = _InProcessTokenBucket(rate=50, capacity=1)
    start = time.monotonic()
    for _ in range(5):
        bucket.acquire()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.06


def test_get_portal_limiter_disabled_when_rps_non_positive():
    limiter = get_portal_limiter(0)
    assert isinstance(limiter, _NoopLimiter)
    start = time.monotonic()
    for _ in range(1000):
        limiter.acquire()
    assert time.monotonic() - start < 0.05


def test_get_portal_limiter_defaults_to_in_process_without_redis_url():
    limiter = get_portal_limiter(10)
    assert isinstance(limiter, _InProcessTokenBucket)


def test_get_portal_limiter_falls_back_when_redis_unreachable():
    # Port chosen to be almost certainly closed; connect timeout is 1s.
    limiter = get_portal_limiter(10, redis_url='redis://127.0.0.1:6399')
    assert isinstance(limiter, _InProcessTokenBucket)


def test_get_portal_limiter_respects_burst_capacity():
    limiter = get_portal_limiter(10, burst=3)
    assert limiter.capacity == 3
    assert limiter.rate == 10


def test_rate_limited_session_acquires_before_request(mocker):
    from genomic_data_service.region_indexer import RateLimitedSession

    calls = []

    class StubLimiter:
        def acquire(self, tokens=1):
            calls.append('acquire')

    mocker.patch(
        'requests.Session.request',
        side_effect=lambda *a, **k: calls.append('request'),
    )
    session = RateLimitedSession(limiter=StubLimiter())
    session.request('GET', 'https://example.com')

    assert calls == ['acquire', 'request']


def test_rate_limited_session_without_limiter_does_not_block(mocker):
    from genomic_data_service.region_indexer import RateLimitedSession

    request = mocker.patch('requests.Session.request', return_value='resp')
    session = RateLimitedSession()  # limiter is None
    assert session.request('GET', 'https://example.com') == 'resp'
    request.assert_called_once()
