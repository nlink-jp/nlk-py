# Changelog

## v0.2.1 (2026-04-12)

### Fixes

- jsonfix: handle zero-width Unicode spaces (U+200B, U+FEFF, U+180E) as whitespace
- jsonfix: skip prose parentheses like `(note):` instead of treating them as tuple starts

## v0.2.0 (2026-04-12)

### Security

- **Breaking:** guard: `wrap()` now raises `ValueError` if input data contains the tag name (defense-in-depth)
- guard: document that Tag must be generated per LLM call (never reuse across turns)
- jsonfix: add JSON smuggling risk note to `extract()` docstring
- strip: add input size warning to `think_tags()` docstring

### Docs

- Add reference manual (`docs/en/reference.md`, `docs/ja/reference.ja.md`)

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
