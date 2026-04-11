# nlk (Python)

Lightweight LLM utility toolkit for [nlink-jp](https://github.com/nlink-jp) projects. Python edition.

A toolbox of small, independent modules for the code that surrounds LLM API calls — not the calls themselves. Zero external dependencies.

See also: [nlk (Go)](https://github.com/nlink-jp/nlk)

## Modules

| Module | Description |
|--------|-------------|
| [`guard`](src/nlk/guard.py) | Nonce-tagged XML wrapping for prompt injection defense (128-bit nonce) |
| [`jsonfix`](src/nlk/jsonfix.py) | Recursive descent JSON parser with repair — single quotes, trailing commas, comments, unquoted keys, escaped JSON, and more |
| [`strip`](src/nlk/strip.py) | Remove LLM thinking/reasoning tags (DeepSeek R1, Qwen, Gemma 4, etc.) |
| [`backoff`](src/nlk/backoff.py) | Exponential backoff duration calculation with jitter |
| [`validate`](src/nlk/validate.py) | Rule-based LLM output validation framework |

## Install

```bash
pip install nlk
```

## Usage

### guard — Prompt injection defense

```python
from nlk.guard import Tag

tag = Tag.new()
wrapped = tag.wrap(untrusted_input)
system_prompt = tag.expand("Data is inside {{DATA_TAG}} tags.")
```

### jsonfix — LLM output repair

```python
from nlk.jsonfix import extract, extract_to

result = extract("```json\n{'key': 'value', 'active': True,}\n```")
data = extract_to("{'category': 'safe', 'confidence': 0.9,}")
```

### strip — Remove LLM thinking tags

```python
from nlk.strip import think_tags

cleaned = think_tags("<think>\nAnalyzing...\n</think>\nThe answer.")
```

### backoff — Exponential backoff

```python
import time
from nlk.backoff import duration

for attempt in range(5):
    result = call_api()
    if result: break
    time.sleep(duration(attempt))

# Custom: time.sleep(duration(attempt, base=2.0, max_delay=60.0))
```

### validate — LLM output validation

```python
from nlk.validate import run, one_of, range_check, max_len, not_empty

err = run(
    one_of("category", result["category"], "safe", "phishing", "spam"),
    range_check("confidence", result["confidence"], 0, 1),
    max_len("tags", len(result["tags"]), 5),
    not_empty("summary", result["summary"]),
)
```

## Design Principles

- **Toolbox, not framework** — each module is independent, use what you need
- **No LLM API abstraction** — your app calls the LLM, nlk handles the surrounding concerns
- **Zero external dependencies** — standard library only, supply chain safe
- **Pure functions** — no side effects, easy to test

## License

MIT (see [LICENSE](LICENSE) for third-party notices)
