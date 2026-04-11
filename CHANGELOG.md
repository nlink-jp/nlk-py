# Changelog

## v0.1.0 (2026-04-11)

Initial release. Python port of [nlk (Go)](https://github.com/nlink-jp/nlk).

### Modules

- `guard` — nonce-tagged XML wrapping for prompt injection defense (128-bit)
- `jsonfix` — recursive descent JSON parser with repair
- `strip` — LLM thinking/reasoning tag removal
- `backoff` — exponential backoff duration calculation with jitter
- `validate` — rule-based LLM output validation

### Design

- Zero external dependencies (standard library only)
- 100 tests passing
- Python 3.10+
