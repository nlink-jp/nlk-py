# AGENTS.md — nlk-py

## Summary

Python edition of nlk — lightweight LLM utility toolkit.
Same 5 modules as Go version, same API design, zero external dependencies.

## Build & Test

```bash
uv run --with pytest pytest tests/ -v
```

## Project Structure

```
nlk-py/
├── src/nlk/
│   ├── __init__.py
│   ├── guard.py       # Nonce-tagged XML wrapping
│   ├── jsonfix.py     # Recursive descent JSON parser with repair
│   ├── strip.py       # LLM thinking/reasoning tag removal
│   ├── backoff.py     # Exponential backoff calculation
│   └── validate.py    # Rule-based validation
├── tests/
│   ├── test_guard.py
│   ├── test_jsonfix.py
│   ├── test_strip.py
│   ├── test_backoff.py
│   └── test_validate.py
├── pyproject.toml
├── README.md
├── README.ja.md
└── LICENSE
```

## Gotchas

- jsonfix parser is inspired by Python json-repair (MIT, Stefano Baccianella) — see LICENSE
- guard uses secrets.token_hex (CSPRNG) for 128-bit nonces
- backoff uses random.uniform (not CSPRNG) — intentional for jitter
- validate.range_check (not range) to avoid Python builtin collision
