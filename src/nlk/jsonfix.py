"""Extract and repair JSON from arbitrary text.

Uses a recursive descent parser to handle common LLM output issues:
single quotes, trailing commas, comments, unquoted keys, missing braces,
escaped JSON, markdown fences, and more.

Inspired by Python json-repair (MIT, Copyright 2023 Stefano Baccianella).
This is an independent implementation, not a port.

Usage::

    from nlk import jsonfix

    result = jsonfix.extract("```json\\n{'key': 'value',}\\n```")
    data = jsonfix.extract_to("...", dict)
"""

import json


class JsonFixError(Exception):
    """Base exception for jsonfix errors."""


class NoJsonError(JsonFixError):
    """No JSON structure found in the input."""


class UnfixableError(JsonFixError):
    """Repaired output is still not valid JSON."""


def extract(text: str) -> str:
    """Find and repair JSON in the input text.

    Note: the input is fully loaded into memory. Callers should limit
    input size before calling if processing untrusted or unbounded data.

    Security note: heuristic repairs may produce a JSON structure that
    differs from the LLM's original intent (JSON smuggling). Always
    validate the deserialized output — for example with
    :mod:`nlk.validate` — before acting on it.

    Raises:
        NoJsonError: No JSON structure found.
        UnfixableError: Repaired output is still invalid.
    """
    if not text:
        raise NoJsonError("empty input")

    # Try as-is first.
    result = _try_parse(text)
    if result is not None:
        return result

    # If input looks like escaped JSON, unescape and retry.
    if '\\"' in text and ('{\\"' in text or '[\\"' in text):
        unescaped = _unescape_json(text)
        if unescaped != text:
            result = _try_parse(unescaped)
            if result is not None:
                return result

    raise UnfixableError("could not extract valid JSON")


def extract_to(text: str, target_type: type | None = None) -> dict | list:
    """Extract JSON and parse into a Python object.

    Args:
        text: Input text containing JSON.
        target_type: Ignored (for API compatibility). Always returns dict/list.

    Returns:
        Parsed JSON as dict or list.
    """
    s = extract(text)
    return json.loads(s)


def _try_parse(text: str) -> str | None:
    """Run the repair parser and validate the result."""
    p = _Parser(text)
    result = p.repair()
    if not result:
        return None
    try:
        json.loads(result)
        return result
    except json.JSONDecodeError:
        return None


def _unescape_json(text: str) -> str:
    """Unescape double-escaped JSON strings."""
    out = []
    i = 0
    chars = list(text)
    while i < len(chars):
        if chars[i] == '\\' and i + 1 < len(chars):
            nxt = chars[i + 1]
            if nxt == '"':
                out.append('"')
                i += 2
            elif nxt == '\\':
                out.append('\\')
                i += 2
            elif nxt == 'n':
                out.append('\n')
                i += 2
            elif nxt == 't':
                out.append('\t')
                i += 2
            else:
                out.append(chars[i])
                i += 1
        else:
            out.append(chars[i])
            i += 1
    return "".join(out)


_ZERO_WIDTH_SPACES = frozenset("\u200b\ufeff\u180e")


def _is_json_space(ch: str) -> bool:
    """Check if character is whitespace, including zero-width Unicode spaces."""
    return ch.isspace() or ch in _ZERO_WIDTH_SPACES


class _Parser:
    """Recursive descent JSON parser with repair capabilities."""

    def __init__(self, text: str) -> None:
        self._input = text
        self._pos = 0
        self._out: list[str] = []

    def repair(self) -> str:
        self._skip_non_json()
        if self._at_end():
            return ""
        self._parse_value()
        return "".join(self._out)

    # --- Navigation ---

    def _peek(self) -> str:
        if self._pos >= len(self._input):
            return ""
        return self._input[self._pos]

    def _peek_at(self, offset: int) -> str:
        i = self._pos + offset
        if i < 0 or i >= len(self._input):
            return ""
        return self._input[i]

    def _advance(self) -> str:
        if self._pos >= len(self._input):
            return ""
        ch = self._input[self._pos]
        self._pos += 1
        return ch

    def _emit(self, s: str) -> None:
        self._out.append(s)

    def _at_end(self) -> bool:
        return self._pos >= len(self._input)

    def _match_prefix(self, s: str) -> bool:
        return self._input[self._pos:self._pos + len(s)] == s

    def _match_prefix_ci(self, s: str) -> bool:
        chunk = self._input[self._pos:self._pos + len(s)]
        if chunk.lower() != s.lower():
            return False
        # Ensure complete token.
        end = self._pos + len(s)
        if end < len(self._input) and self._input[end].isalpha():
            return False
        return True

    # --- Whitespace / comments ---

    def _skip_ws(self) -> None:
        while not self._at_end() and _is_json_space(self._input[self._pos]):
            self._pos += 1

    def _skip_ws_and_comments(self) -> None:
        while True:
            self._skip_ws()
            if self._at_end():
                return
            if self._peek() == '/' and self._peek_at(1) == '/':
                self._pos += 2
                while not self._at_end() and self._peek() != '\n':
                    self._advance()
                continue
            if self._peek() == '/' and self._peek_at(1) == '*':
                self._pos += 2
                while not self._at_end():
                    if self._peek() == '*' and self._peek_at(1) == '/':
                        self._pos += 2
                        break
                    self._advance()
                continue
            if self._peek() == '#':
                self._advance()
                while not self._at_end() and self._peek() != '\n':
                    self._advance()
                continue
            break

    def _skip_non_json(self) -> None:
        """Skip until we find { [ or a tuple-like (."""
        while not self._at_end():
            self._skip_ws_and_comments()
            if self._at_end():
                return
            if self._match_prefix("```"):
                self._pos += 3
                while not self._at_end() and self._peek() != '\n':
                    self._advance()
                if not self._at_end():
                    self._advance()
                continue
            ch = self._peek()
            if ch in ('{', '['):
                return
            if ch == '(' and self._looks_like_tuple():
                return
            self._advance()

    def _looks_like_tuple(self) -> bool:
        """Check if '(' starts a tuple rather than prose parentheses."""
        i = self._pos + 1  # skip '('
        while i < len(self._input) and _is_json_space(self._input[i]):
            i += 1
        if i >= len(self._input):
            return False
        ch = self._input[i]
        if ch in ('"', "'", '{', '[', '(', '-', '.'):
            return True
        if ch.isdigit():
            return True
        remaining = self._input[i:]
        for lit in ("true", "false", "null", "none", "True", "False", "None", "NULL"):
            if remaining.startswith(lit):
                end = i + len(lit)
                if end >= len(self._input) or not self._input[end].isalpha():
                    return True
        return False

    # --- Value ---

    def _parse_value(self) -> None:
        self._skip_ws_and_comments()
        if self._at_end():
            return

        ch = self._peek()

        if ch == '{':
            self._parse_object()
        elif ch in ('[', '('):
            self._parse_array()
        elif ch == '"':
            self._parse_string('"')
        elif ch == "'":
            self._parse_string("'")
        elif ch in ('t', 'f', 'n'):
            self._parse_literal()
        elif ch in ('T', 'F', 'N'):
            self._parse_literal_upper()
        elif ch == '.' and self._match_prefix("..."):
            self._pos += 3
        elif ch in ('-', '.') or ch.isdigit():
            self._parse_number()
        else:
            self._parse_unquoted_value()

    # --- Object ---

    def _parse_object(self) -> None:
        self._advance()  # {
        self._emit('{')
        first = True

        while True:
            self._skip_ws_and_comments()
            if self._at_end():
                self._emit('}')
                return

            ch = self._peek()

            if ch == '}':
                self._advance()
                self._emit('}')
                return

            if ch == ',':
                self._advance()
                self._skip_ws_and_comments()
                if self._at_end() or self._peek() == '}':
                    if not self._at_end():
                        self._advance()
                    self._emit('}')
                    return
                if not first:
                    self._emit(',')
            elif not first:
                self._emit(',')

            first = False

            # Key.
            self._skip_ws_and_comments()
            if self._at_end():
                self._emit('}')
                return
            self._parse_key()

            # Colon.
            self._skip_ws_and_comments()
            if not self._at_end() and self._peek() == ':':
                self._advance()
            self._emit(':')

            # Value.
            self._skip_ws_and_comments()
            if self._at_end() or self._peek() in ('}', ','):
                self._emit('""')
                continue
            self._parse_value()

    def _parse_key(self) -> None:
        ch = self._peek()
        if ch == '"':
            self._parse_string('"')
        elif ch == "'":
            self._parse_string("'")
        else:
            self._parse_unquoted_key()

    def _parse_unquoted_key(self) -> None:
        self._emit('"')
        while not self._at_end():
            ch = self._peek()
            if ch in (':', ' ', '\t', '\n', '\r', '}'):
                break
            self._emit(self._advance())
        self._emit('"')

    # --- Array ---

    def _parse_array(self) -> None:
        open_ch = self._advance()  # [ or (
        self._emit('[')
        closing = ')' if open_ch == '(' else ']'
        first = True

        while True:
            self._skip_ws_and_comments()
            if self._at_end():
                self._emit(']')
                return

            ch = self._peek()

            if ch == closing or (closing == ')' and ch == ')') or ch == ']':
                self._advance()
                self._emit(']')
                return

            if ch == ',':
                self._advance()
                self._skip_ws_and_comments()
                if self._at_end() or self._peek() in (closing, ']'):
                    if not self._at_end():
                        self._advance()
                    self._emit(']')
                    return
                if not first:
                    self._emit(',')
            elif not first:
                self._emit(',')

            first = False

            # Handle ellipsis.
            self._skip_ws_and_comments()
            if self._match_prefix("..."):
                self._pos += 3
                # Undo the comma we just emitted.
                if self._out and self._out[-1] == ',':
                    self._out.pop()
                first = True
                continue

            self._parse_value()

    # --- String ---

    def _parse_string(self, quote: str) -> None:
        self._advance()  # opening quote
        self._emit('"')

        while not self._at_end():
            ch = self._peek()

            if ch in ('\n', '\r'):
                self._emit('"')
                return

            if ch == '\\':
                self._advance()
                if self._at_end():
                    self._emit('"')
                    return
                nxt = self._advance()
                if nxt in ('"', '\\', '/', 'b', 'f', 'n', 'r', 't'):
                    self._emit('\\')
                    self._emit(nxt)
                elif nxt == "'":
                    self._emit("'")
                elif nxt == 'u':
                    self._emit('\\u')
                    for _ in range(4):
                        if not self._at_end():
                            self._emit(self._advance())
                elif nxt == 'x':
                    self._emit('\\u00')
                    for _ in range(2):
                        if not self._at_end():
                            self._emit(self._advance())
                else:
                    self._emit(nxt)
                continue

            if ch == quote:
                # Look ahead: is this the real closing quote?
                nxt = self._peek_ahead_skip_space(1)
                if nxt in (':', ',', '}', ']', ')', ''):
                    self._advance()
                    self._emit('"')
                    return
                # Internal unescaped quote — escape it.
                self._advance()
                self._emit('\\"')
                continue

            self._emit(self._advance())

        self._emit('"')

    def _peek_ahead_skip_space(self, offset: int) -> str:
        i = self._pos + offset
        while i < len(self._input) and _is_json_space(self._input[i]):
            i += 1
        if i >= len(self._input):
            return ""
        return self._input[i]

    # --- Unquoted value ---

    def _parse_unquoted_value(self) -> None:
        buf: list[str] = []
        while not self._at_end():
            ch = self._peek()
            if ch in (',', '}', ']', ':', '\n'):
                break
            buf.append(self._advance())

        val = "".join(buf).strip()
        if val.endswith("```"):
            val = val[:-3].strip()

        if not val:
            self._emit('""')
            return

        self._emit('"')
        for c in val:
            if c == '"':
                self._emit('\\"')
            else:
                self._emit(c)
        self._emit('"')

    # --- Literals ---

    def _parse_literal(self) -> None:
        if self._match_prefix("true"):
            self._pos += 4
            self._emit("true")
        elif self._match_prefix("false"):
            self._pos += 5
            self._emit("false")
        elif self._match_prefix("null"):
            self._pos += 4
            self._emit("null")
        else:
            self._parse_unquoted_value()

    def _parse_literal_upper(self) -> None:
        if self._match_prefix_ci("true"):
            self._pos += 4
            self._emit("true")
        elif self._match_prefix_ci("false"):
            self._pos += 5
            self._emit("false")
        elif self._match_prefix_ci("null"):
            self._pos += 4
            self._emit("null")
        elif self._match_prefix_ci("none"):
            self._pos += 4
            self._emit("null")
        else:
            self._parse_unquoted_value()

    # --- Numbers ---

    def _parse_number(self) -> None:
        if self._peek() == '.':
            self._emit('0')

        if self._peek() == '-':
            self._emit(self._advance())

        has_digit = False

        while not self._at_end() and self._peek().isdigit():
            self._emit(self._advance())
            has_digit = True
            if not self._at_end() and self._peek() == '_':
                self._advance()

        if not self._at_end() and self._peek() == '.':
            nxt = self._peek_at(1)
            if nxt.isdigit():
                self._emit(self._advance())  # .
                while not self._at_end() and self._peek().isdigit():
                    self._emit(self._advance())
                    if not self._at_end() and self._peek() == '_':
                        self._advance()
            elif has_digit:
                self._advance()  # skip trailing dot
                self._emit('.0')

        if not self._at_end() and self._peek() in ('e', 'E'):
            self._emit(self._advance())
            if not self._at_end() and self._peek() in ('+', '-'):
                self._emit(self._advance())
            while not self._at_end() and self._peek().isdigit():
                self._emit(self._advance())
