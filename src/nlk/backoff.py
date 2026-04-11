"""Exponential backoff duration calculation with jitter.

Computes wait durations only — does not sleep or retry.
The calling application controls the retry loop.

Usage::

    import time
    from nlk import backoff

    for attempt in range(5):
        result = call_api()
        if result: break
        time.sleep(backoff.duration(attempt))
"""

import random

DEFAULT_BASE = 5.0
DEFAULT_MAX = 120.0
DEFAULT_JITTER = 1.0


def duration(
    attempt: int,
    *,
    base: float = DEFAULT_BASE,
    max_delay: float = DEFAULT_MAX,
    jitter: float = DEFAULT_JITTER,
) -> float:
    """Return the wait duration in seconds for the given attempt (0-indexed).

    Formula: min(base * 2^attempt, max_delay) + uniform(-jitter, +jitter)
    Result is clamped to a minimum of 0.

    Args:
        attempt: Retry attempt number (0-indexed). Negative values are treated as 0.
        base: Base delay in seconds. Default 5.0.
        max_delay: Maximum delay cap in seconds. Default 120.0.
        jitter: Jitter range in seconds. Actual jitter is uniform in
            [-jitter, +jitter]. Default 1.0.

    Returns:
        Wait duration in seconds.
    """
    if attempt < 0:
        attempt = 0

    delay = min(base * (2 ** attempt), max_delay)

    if jitter > 0:
        delay += random.uniform(-jitter, jitter)

    return max(delay, 0.0)
