"""Nonce-tagged XML wrapping for prompt injection defense.

Wraps untrusted data in XML tags containing a cryptographic nonce,
making it physically distinct from system instructions in the prompt.

Usage::

    tag = Tag.new()
    wrapped = tag.wrap(untrusted_input)
    system_prompt = tag.expand("Data is inside {{DATA_TAG}} tags.")
"""

import secrets

NONCE_SIZE = 16
DEFAULT_PLACEHOLDER = "{{DATA_TAG}}"


class Tag:
    """A nonce-based XML tag for isolating untrusted data."""

    __slots__ = ("_name",)

    def __init__(self, name: str) -> None:
        self._name = name

    @staticmethod
    def new(prefix: str = "user_data") -> "Tag":
        """Generate a new Tag with a cryptographically random nonce.

        Args:
            prefix: Tag name prefix. Default "user_data".

        Returns:
            Tag with name like "user_data_a1b2c3d4e5f6a7b8..."
        """
        nonce = secrets.token_hex(NONCE_SIZE)
        return Tag(f"{prefix}_{nonce}")

    @property
    def name(self) -> str:
        """The tag name (e.g. "user_data_a1b2c3d4...")."""
        return self._name

    def wrap(self, data: str) -> str:
        """Enclose data in XML tags: <tagname>data</tagname>."""
        return f"<{self._name}>{data}</{self._name}>"

    def expand(self, template: str, placeholder: str = DEFAULT_PLACEHOLDER) -> str:
        """Replace placeholder in the template with the tag name."""
        return template.replace(placeholder, self._name)
