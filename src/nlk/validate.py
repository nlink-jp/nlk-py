"""Rule-based LLM output validation.

Applications define rules; this module handles execution and error collection.

Usage::

    from nlk import validate

    err = validate.run(
        validate.one_of("category", result["category"], "safe", "phishing"),
        validate.range_check("confidence", result["confidence"], 0, 1),
        validate.max_len("tags", len(result["tags"]), 5),
    )
"""

from typing import Callable

Rule = Callable[[], str | None]
"""A validation rule. Returns None if valid, or an error message string."""


def run(*rules: Rule) -> str | None:
    """Execute all rules and return a combined error if any fail.

    Returns None if all rules pass, or a semicolon-separated error string.
    """
    errs = [msg for r in rules if (msg := r()) is not None]
    return "; ".join(errs) if errs else None


def errors(*rules: Rule) -> list[str] | None:
    """Execute all rules and return individual errors as a list.

    Returns None if all rules pass.
    """
    errs = [msg for r in rules if (msg := r()) is not None]
    return errs if errs else None


# --- Built-in rule constructors ---


def one_of(field: str, value: str, *allowed: str) -> Rule:
    """Check that value is one of the allowed values."""
    def _check() -> str | None:
        if value in allowed:
            return None
        opts = ", ".join(allowed)
        return f'{field}: "{value}" is not one of [{opts}]'
    return _check


def range_check(field: str, value: float, min_val: float, max_val: float) -> Rule:
    """Check that value is within [min_val, max_val]."""
    def _check() -> str | None:
        if min_val <= value <= max_val:
            return None
        return f"{field}: {value} is out of range [{min_val}, {max_val}]"
    return _check


def max_len(field: str, length: int, max_val: int) -> Rule:
    """Check that length does not exceed max_val."""
    def _check() -> str | None:
        if length <= max_val:
            return None
        return f"{field}: length {length} exceeds max {max_val}"
    return _check


def not_empty(field: str, value: str) -> Rule:
    """Check that value is not empty or whitespace-only."""
    def _check() -> str | None:
        if value.strip():
            return None
        return f"{field}: must not be empty"
    return _check


def custom(field: str, fn: Callable[[], str | None]) -> Rule:
    """Create a rule from an arbitrary function."""
    def _check() -> str | None:
        msg = fn()
        if msg is None:
            return None
        return f"{field}: {msg}"
    return _check
