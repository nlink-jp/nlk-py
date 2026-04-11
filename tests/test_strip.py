from nlk.strip import think_tags, tags


def test_deepseek_think():
    raw = "<think>\nLet me analyze...\nSuspicious.\n</think>\nThe answer."
    assert think_tags(raw) == "The answer."


def test_empty_think():
    assert think_tags("<think>\n</think>\nThe answer.") == "The answer."


def test_unclosed_think():
    assert think_tags("<think>\nStill thinking...") == ""


def test_unclosed_with_preamble():
    assert think_tags("Preamble\n<think>\nThinking...") == "Preamble"


def test_thinking_tags():
    assert think_tags("<thinking>Step 1...</thinking>\nResult") == "Result"


def test_reasoning_tags():
    assert think_tags('<reasoning>Analyzing...</reasoning>\n{"safe": true}') == '{"safe": true}'


def test_reflection_tags():
    assert think_tags("<reflection>Reconsidering...</reflection>\nFinal") == "Final"


def test_case_insensitive():
    assert think_tags("<THINK>Uppercase</THINK>\nResult") == "Result"


def test_no_tags():
    text = "Just normal text."
    assert think_tags(text) == text


def test_empty_input():
    assert think_tags("") == ""


def test_with_json():
    raw = '<think>\nAnalyzing...\n</think>\n{"category": "phishing"}'
    assert think_tags(raw) == '{"category": "phishing"}'


def test_multiple_blocks():
    raw = "<think>First</think>\nPart 1\n<think>Second</think>\nPart 2"
    result = think_tags(raw)
    assert "First" not in result
    assert "Second" not in result
    assert "Part 1" in result
    assert "Part 2" in result


def test_gemma4():
    raw = "<|channel>thought\nReasoning here.\n<channel|>\nThe answer."
    assert think_tags(raw) == "The answer."


def test_gemma4_unclosed():
    assert think_tags("<|channel>thought\nReasoning...") == ""


def test_gemma4_with_content():
    raw = "Preamble\n<|channel>thought\nInternal\n<channel|>\nFinal"
    result = think_tags(raw)
    assert "Preamble" in result
    assert "Final" in result
    assert "Internal" not in result


def test_custom_tags():
    assert tags("<analysis>Notes</analysis>\nPublic", "analysis") == "Public"


def test_custom_tags_multiple():
    raw = "<step1>Plan</step1>\n<step2>Execute</step2>\nDone"
    assert tags(raw, "step1", "step2") == "Done"


def test_custom_tags_no_match():
    text = "No matching tags"
    assert tags(text, "nonexistent") == text
