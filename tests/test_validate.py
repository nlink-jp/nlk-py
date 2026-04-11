from nlk.validate import run, errors, one_of, range_check, max_len, not_empty, custom


def test_run_all_pass():
    assert run(
        one_of("cat", "safe", "safe", "phishing"),
        range_check("conf", 0.5, 0, 1),
        max_len("tags", 3, 5),
    ) is None


def test_run_single_failure():
    err = run(one_of("cat", "unknown", "safe", "phishing"))
    assert err is not None
    assert "cat" in err


def test_run_multiple_failures():
    err = run(
        one_of("cat", "bad", "safe", "phishing"),
        range_check("conf", 1.5, 0, 1),
        max_len("tags", 10, 5),
    )
    assert "cat" in err
    assert "conf" in err
    assert "tags" in err


def test_run_empty():
    assert run() is None


def test_errors_list():
    errs = errors(
        one_of("a", "x", "y", "z"),
        range_check("b", 0.5, 0, 1),  # pass
        max_len("c", 10, 5),
    )
    assert len(errs) == 2


def test_errors_all_pass():
    assert errors(range_check("x", 0.5, 0, 1)) is None


def test_one_of_pass():
    assert one_of("f", "safe", "safe", "phishing")() is None

def test_one_of_fail():
    assert one_of("f", "unknown", "safe", "phishing")() is not None

def test_one_of_empty():
    assert one_of("f", "", "safe")() is not None


def test_range_pass():
    assert range_check("f", 0.5, 0, 1)() is None
    assert range_check("f", 0, 0, 1)() is None
    assert range_check("f", 1, 0, 1)() is None

def test_range_fail():
    assert range_check("f", -0.1, 0, 1)() is not None
    assert range_check("f", 1.1, 0, 1)() is not None


def test_max_len_pass():
    assert max_len("f", 3, 5)() is None
    assert max_len("f", 5, 5)() is None

def test_max_len_fail():
    assert max_len("f", 6, 5)() is not None


def test_not_empty_pass():
    assert not_empty("f", "hello")() is None

def test_not_empty_fail():
    assert not_empty("f", "")() is not None
    assert not_empty("f", "  ")() is not None
    assert not_empty("f", "\t\n")() is not None


def test_custom_pass():
    assert custom("f", lambda: None)() is None

def test_custom_fail():
    err = custom("f", lambda: "bad value")()
    assert "f" in err
    assert "bad value" in err


def test_mail_analyzer_pattern():
    j = {
        "category": "phishing",
        "confidence": 0.87,
        "tags": ["a", "b"],
        "reasons": ["r1", "r2"],
        "summary": "Suspicious email.",
    }
    assert run(
        one_of("category", j["category"],
               "phishing", "spam", "malware-delivery", "bec", "scam", "safe"),
        range_check("confidence", j["confidence"], 0, 1),
        max_len("tags", len(j["tags"]), 5),
        max_len("reasons", len(j["reasons"]), 5),
        not_empty("summary", j["summary"]),
    ) is None
