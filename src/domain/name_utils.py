"""Utility functions for name processing."""

# Portuguese particles to filter out of names
_PARTICLES = {"de", "do", "dos", "da", "das", "di", "du"}


def format_display_name(full_name: str) -> str:
    """Format a full name for display: First M. M. Last (no particles).

    Rules:
    1. Strip whitespace, split into tokens.
    2. Remove Portuguese particles (de, do, dos, da, das, di, du).
    3. Single token → title-cased.
    4. Two tokens → "First Last", title-cased.
    5. Three+ tokens → "First M. M. Last" with abbreviated middles.

    Args:
        full_name: The full name string.

    Returns:
        Formatted display name.

    Examples:
        >>> format_display_name("Antonio Ismael Rodrigues de Melo")
        'Antonio I. R. Melo'
        >>> format_display_name("Fabio Akita")
        'Fabio Akita'
        >>> format_display_name("Marvin")
        'Marvin'
        >>> format_display_name("guilherme da silva")
        'Guilherme Silva'
    """
    name = full_name.strip()
    if not name:
        return ""

    tokens = name.split()
    # Filter out particles (case-insensitive)
    filtered = [t for t in tokens if t.lower() not in _PARTICLES]

    if not filtered:
        return ""

    if len(filtered) == 1:
        return filtered[0].title()

    if len(filtered) == 2:
        return f"{filtered[0].title()} {filtered[1].title()}"

    # 3+ tokens: First + abbreviated middles + Last
    first = filtered[0].title()
    last = filtered[-1].title()
    middle_tokens = filtered[1:-1]
    middles = [f"{m[0].upper()}." for m in middle_tokens]

    return f"{first} {' '.join(middles)} {last}"
