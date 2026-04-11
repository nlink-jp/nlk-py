from nlk.backoff import duration, DEFAULT_BASE, DEFAULT_MAX, DEFAULT_JITTER


def test_defaults_attempt_0():
    d = duration(0)
    assert 4.0 <= d <= 6.0  # 5s ± 1s jitter


def test_defaults_attempt_1():
    d = duration(1)
    assert 9.0 <= d <= 11.0  # 10s ± 1s


def test_defaults_attempt_2():
    d = duration(2)
    assert 19.0 <= d <= 21.0  # 20s ± 1s


def test_max_cap():
    d = duration(2, base=10.0, max_delay=30.0, jitter=0.0)
    assert d == 30.0  # 10 * 4 = 40 → capped to 30


def test_no_jitter():
    for attempt in range(6):
        d = duration(attempt, base=1.0, max_delay=60.0, jitter=0.0)
        expected = min(2 ** attempt, 60.0)
        assert d == expected, f"attempt {attempt}: {d} != {expected}"


def test_jitter_range():
    for _ in range(100):
        d = duration(0, base=10.0, max_delay=120.0, jitter=2.0)
        assert 8.0 <= d <= 12.0


def test_non_negative():
    for _ in range(200):
        d = duration(0, base=0.1, max_delay=1.0, jitter=0.5)
        assert d >= 0.0


def test_negative_attempt():
    d = duration(-1, base=1.0, max_delay=60.0, jitter=0.0)
    assert d == 1.0


def test_very_negative_attempt():
    d = duration(-100, base=1.0, max_delay=60.0, jitter=0.0)
    assert d == 1.0


def test_exponential_growth():
    prev = duration(0, base=1.0, max_delay=1000.0, jitter=0.0)
    for attempt in range(1, 8):
        d = duration(attempt, base=1.0, max_delay=1000.0, jitter=0.0)
        assert d >= prev
        prev = d
