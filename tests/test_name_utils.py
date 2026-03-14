"""Tests for name utility functions."""

from src.domain.name_utils import extract_short_name


class TestExtractShortName:
    """Tests for the extract_short_name function."""

    def test_two_words(self) -> None:
        """Two-word name stays as-is."""
        assert extract_short_name("Fabio Akita") == "Fabio Akita"

    def test_single_word(self) -> None:
        """Single-word name stays as-is."""
        assert extract_short_name("Marvin") == "Marvin"

    def test_multiple_words(self) -> None:
        """Multi-word name returns first and last."""
        assert (
            extract_short_name("Matheus Willian dos Santos Torriciello")
            == "Matheus Torriciello"
        )

    def test_three_words(self) -> None:
        """Three-word name returns first and last."""
        assert extract_short_name("João Pedro Diniz") == "João Diniz"

    def test_whitespace_trimming(self) -> None:
        """Leading/trailing whitespace is stripped."""
        assert extract_short_name("  Rafa  ") == "Rafa"

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        assert extract_short_name("") == ""

    def test_whitespace_only(self) -> None:
        """Whitespace-only string returns empty string."""
        assert extract_short_name("   ") == ""

    def test_name_with_extra_spaces(self) -> None:
        """Name with extra internal spaces works correctly."""
        assert extract_short_name("  Ana  Clara  Ritter  ") == "Ana Ritter"

    def test_long_name(self) -> None:
        """Long multi-part name returns first and last."""
        assert (
            extract_short_name("Victor Manuel guedes cavalcante")
            == "Victor cavalcante"
        )

    def test_name_with_pipe_character(self) -> None:
        """Name containing pipe character processes correctly."""
        assert (
            extract_short_name("Edson Damianni | Lançador 6 em 7")
            == "Edson 7"
        )
