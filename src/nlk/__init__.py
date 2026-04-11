"""nlk — Lightweight LLM utility toolkit.

A toolbox of small, independent modules for the code that surrounds
LLM API calls — not the calls themselves. Zero external dependencies.

Modules:
    guard    — Nonce-tagged XML wrapping for prompt injection defense
    jsonfix  — JSON extraction and repair from LLM output
    strip    — Remove LLM thinking/reasoning tags
    backoff  — Exponential backoff duration calculation with jitter
    validate — Rule-based LLM output validation
"""

__version__ = "0.1.0"
