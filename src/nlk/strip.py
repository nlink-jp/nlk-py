"""Remove LLM thinking/reasoning tags from model output.

Supports DeepSeek R1 (<think>), Qwen (<think>), Gemma 4
(<|channel>thought...<channel|>), and other common formats.

Usage::

    from nlk import strip

    cleaned = strip.think_tags(llm_output)
    # or with custom tag names:
    cleaned = strip.tags(llm_output, "analysis", "internal")
"""

import re


def think_tags(text: str) -> str:
    """Remove all known thinking/reasoning tag patterns.

    Handles: <think>, <thinking>, <reasoning>, <reflection>,
    Gemma 4 channel format, empty tags, unclosed tags.

    Note: the input is fully loaded into memory. Callers should limit
    input size before calling if processing untrusted or unbounded data.
    """
    result = tags(text, "think", "thinking", "reasoning", "reflection")
    result = _strip_gemma4_thought(result)
    return result


def tags(text: str, *tag_names: str) -> str:
    """Remove XML-style tag pairs and their content.

    Case-insensitive. Handles unclosed tags (removes to end of text).
    """
    result = text
    for name in tag_names:
        result = _strip_xml_tag(result, name)
    return result


def _strip_xml_tag(text: str, name: str) -> str:
    """Remove all occurrences of <name>...</name> (case-insensitive).

    Skips occurrences inside markdown inline-code spans
    (single-backtick on the same line, e.g. ``\\`<think>\\```). LLM
    responses that EXPLAIN the literal tag — common when the user
    asks "what is <think>?" — would otherwise have everything from
    the literal `<think>` to end-of-text stripped under the
    unclosed-tag rule, truncating the explanation mid-sentence.

    Out of scope: triple-backtick fenced blocks and HTML <code>;
    add when a real symptom motivates it.
    """
    open_tag = f"<{name}>"
    close_tag = f"</{name}>"

    scan_from = 0
    while True:
        open_idx = _index_ci(text[scan_from:], open_tag)
        if open_idx < 0:
            break
        open_idx += scan_from

        if _is_inside_inline_code_span(text, open_idx):
            # Skip just this occurrence; advance past the open tag.
            scan_from = open_idx + len(open_tag)
            continue

        search_from = open_idx + len(open_tag)
        close_idx = _index_ci(text[search_from:], close_tag)

        if close_idx < 0:
            # Unclosed tag — remove to end.
            text = text[:open_idx].strip()
            break

        end_idx = search_from + close_idx + len(close_tag)
        text = text[:open_idx] + text[end_idx:]
        # Resume scanning from the cut point.
        scan_from = open_idx

    return text.strip()


def _is_inside_inline_code_span(text: str, pos: int) -> bool:
    """True if ``pos`` falls inside a single-backtick inline code span.

    Detection: count backticks on the same line strictly before
    ``pos``; odd count means an unclosed span is currently open.
    Lines are delimited by ``\\n``. Triple-backtick fenced blocks
    and HTML ``<code>`` are intentionally NOT modelled.
    """
    if pos <= 0 or pos > len(text):
        return False
    line_start = text.rfind("\n", 0, pos) + 1  # 0 if not found
    return text.count("`", line_start, pos) % 2 == 1


def _strip_gemma4_thought(text: str) -> str:
    """Remove Gemma 4 channel-based thought: <|channel>thought...<channel|>."""
    open_tag = "<|channel>thought"
    close_tag = "<channel|>"

    while True:
        open_idx = text.find(open_tag)
        if open_idx < 0:
            break

        search_from = open_idx + len(open_tag)
        close_idx = text.find(close_tag, search_from)

        if close_idx < 0:
            text = text[:open_idx].strip()
            break

        end_idx = close_idx + len(close_tag)
        text = text[:open_idx] + text[end_idx:]

    return text.strip()


def _index_ci(s: str, substr: str) -> int:
    """Case-insensitive index. Returns -1 if not found."""
    try:
        return s.lower().index(substr.lower())
    except ValueError:
        return -1
