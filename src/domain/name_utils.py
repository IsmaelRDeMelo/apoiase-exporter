"""Utility functions for name processing."""


def extract_short_name(full_name: str) -> str:
    """Extract a short name (first + last) from a full name.

    If the name has only one word, return it as-is.
    If the name has multiple words, return the first and last word.

    Args:
        full_name: The full name string.

    Returns:
        Short name with first and last name only.

    Examples:
        >>> extract_short_name("Fabio Akita")
        'Fabio Akita'
        >>> extract_short_name("Matheus Willian dos Santos Torriciello")
        'Matheus Torriciello'
        >>> extract_short_name("Marvin")
        'Marvin'
        >>> extract_short_name("  Rafa  ")
        'Rafa'
    """
    name = full_name.strip()
    if not name:
        return ""

    parts = name.split()
    if len(parts) <= 2:
        return " ".join(parts)

    return f"{parts[0]} {parts[-1]}"
