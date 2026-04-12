import json
import pytest
from nlk.jsonfix import extract, extract_to, NoJsonError, UnfixableError


def must_extract(name: str, text: str) -> str:
    result = extract(text)
    assert json.loads(result) is not None, f"[{name}] not valid JSON: {result}"
    return result


# --- Basic ---

def test_plain_object():
    must_extract("plain", '{"key": "value", "num": 42}')

def test_plain_array():
    must_extract("array", '[1, 2, 3]')

def test_nested():
    must_extract("nested", '{"a": {"b": {"c": [1, 2, {"d": true}]}}}')

def test_empty_object():
    assert extract("{}") == "{}"

def test_empty_array():
    assert extract("[]") == "[]"

# --- Markdown fences ---

def test_markdown_fence():
    must_extract("fence", '```json\n{"key": "value"}\n```')

def test_fence_no_lang():
    must_extract("fence no lang", '```\n{"a": 1}\n```')

def test_fence_with_text():
    must_extract("fence text", 'Result:\n```json\n{"r": "safe"}\n```\nDone.')

# --- Surrounding text ---

def test_surrounding_text():
    r = must_extract("surrounding", 'Result:\n{"category": "safe"}\nEnd.')
    assert json.loads(r)["category"] == "safe"

# --- Single quotes ---

def test_single_quotes():
    r = must_extract("single", "{'key': 'value', 'num': 42}")
    assert json.loads(r)["key"] == "value"

def test_mixed_quotes():
    must_extract("mixed", """{"key": 'value', 'key2': "value2"}""")

# --- Trailing commas ---

def test_trailing_comma_object():
    must_extract("trailing obj", '{"a": 1, "b": 2,}')

def test_trailing_comma_array():
    must_extract("trailing arr", '[1, 2, 3,]')

def test_trailing_comma_nested():
    must_extract("trailing nested", '{"a": {"b": 1,}, "c": [1, 2,],}')

# --- Unquoted keys ---

def test_unquoted_keys():
    r = must_extract("unquoted", '{key: "value", key2: 42}')
    assert json.loads(r)["key"] == "value"

# --- Comments ---

def test_line_comment():
    must_extract("line comment", '{\n// comment\n"key": "value"\n}')

def test_block_comment():
    must_extract("block comment", '{\n/* comment */\n"key": "value"\n}')

def test_hash_comment():
    must_extract("hash comment", '{\n# comment\n"key": "value"\n}')

# --- Bool/null normalization ---

def test_uppercase_true():
    assert json.loads(extract('{"f": True}'))["f"] is True

def test_uppercase_false():
    assert json.loads(extract('{"f": False}'))["f"] is False

def test_none():
    assert json.loads(extract('{"v": None}'))["v"] is None

def test_null_upper():
    assert json.loads(extract('{"v": NULL}'))["v"] is None

# --- Missing braces ---

def test_missing_closing_brace():
    must_extract("missing brace", '{"key": "value", "nested": {"inner": true}')

def test_missing_closing_bracket():
    must_extract("missing bracket", '[1, 2, 3')

def test_deep_nesting_missing():
    must_extract("deep missing", '{"a": {"b": {"c": [1, 2, 3')

# --- Missing commas ---

def test_missing_comma_object():
    must_extract("missing comma obj", '{"a": "1" "b": "2"}')

def test_missing_comma_array():
    must_extract("missing comma arr", '["a" "b" "c"]')

# --- Python constructs ---

def test_python_tuple():
    r = must_extract("tuple", '("a", "b", "c")')
    assert json.loads(r) == ["a", "b", "c"]

# --- Ellipsis ---

def test_ellipsis():
    r = must_extract("ellipsis", '[1, 2, 3, ...]')
    assert json.loads(r) == [1, 2, 3]

# --- Numbers ---

def test_leading_dot():
    assert json.loads(extract('{"v": .5}'))["v"] == 0.5

def test_trailing_dot():
    assert json.loads(extract('{"v": 1.}'))["v"] == 1.0

def test_underscore_number():
    assert json.loads(extract('{"v": 1_000_000}'))["v"] == 1000000

def test_negative():
    assert json.loads(extract('{"v": -42}'))["v"] == -42

def test_exponent():
    must_extract("exponent", '{"v": 1.5e10}')

# --- Escape handling ---

def test_hex_escape():
    must_extract("hex", r'{"v": "\x41\x42"}')

def test_escaped_json():
    r = must_extract("escaped", r'{\"key\": \"value\", \"num\": 42}')
    assert json.loads(r)["key"] == "value"

def test_unescaped_inner_quote():
    r = must_extract("inner quote", '{"msg": "lorem \\"ipsum\\" dolor"}')
    assert json.loads(r) is not None

# --- Errors ---

def test_empty_input():
    with pytest.raises(NoJsonError):
        extract("")

def test_no_json():
    with pytest.raises((NoJsonError, UnfixableError)):
        extract("Just plain text with no JSON.")

# --- extract_to ---

def test_extract_to():
    r = extract_to("```json\n{'category': 'phishing', 'confidence': 0.87,}\n```")
    assert r["category"] == "phishing"
    assert r["confidence"] == 0.87

# --- Combined ---

def test_combined():
    r = must_extract("combined", "{name: 'John', age: 30, 'active': True,")
    d = json.loads(r)
    assert d["name"] == "John"
    assert d["active"] is True

def test_real_world():
    raw = (
        "Based on my analysis:\n"
        "```json\n"
        "{\n"
        "  'is_suspicious': True,\n"
        "  'category': 'phishing',\n"
        "  'confidence': 0.92,\n"
        "  'reasons': [\n"
        "    'URL on free hosting',\n"
        "    'Mismatch',\n"
        "  ],\n"
        "}\n"
        "```\n"
    )
    d = json.loads(must_extract("real world", raw))
    assert d["category"] == "phishing"
    assert d["is_suspicious"] is True

# --- Japanese ---

def test_japanese():
    r = must_extract("japanese", '{"emoji": "🎉", "jp": "日本語テスト"}')
    assert json.loads(r)["jp"] == "日本語テスト"

# --- Zero-width space handling ---

def test_zero_width_space():
    r = must_extract("zwsp", '{\u200b"key"\u200b:\u200b"value"\u200b}')
    assert json.loads(r)["key"] == "value"

def test_bom():
    r = must_extract("bom", '\ufeff{"key": "value"}')
    assert json.loads(r)["key"] == "value"

def test_mongolian_vowel_separator():
    r = must_extract("mvs", '{\u180e"key":\u180e"value"}')
    d = json.loads(r)
    assert d["key"] == "value"

# --- Parenthesized prose should not hijack JSON ---

def test_paren_prose_before_json():
    r = must_extract("paren prose", '(some clarification):\n{"key": "value"}')
    assert json.loads(r)["key"] == "value"

def test_paren_prose_before_fenced_json():
    raw = '(note: important):\n```json\n{"result": "ok"}\n```'
    r = must_extract("paren fenced", raw)
    assert json.loads(r)["result"] == "ok"

def test_tuple_still_works():
    r = must_extract("tuple", '("a", "b", "c")')
    assert json.loads(r) == ["a", "b", "c"]

def test_tuple_with_numbers():
    r = must_extract("tuple nums", '(1, 2, 3)')
    assert json.loads(r) == [1, 2, 3]

def test_tuple_with_booleans():
    r = must_extract("tuple bools", '(true, false, null)')
    assert json.loads(r) == [True, False, None]
