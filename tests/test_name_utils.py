"""Tests for name utility functions."""

from src.domain.name_utils import format_display_name


class TestFormatDisplayName:
    """Tests for the format_display_name function."""

    def test_two_words(self) -> None:
        """Two-word name stays as first + last, title-cased."""
        assert format_display_name("Fabio Akita") == "Fabio Akita"

    def test_single_word(self) -> None:
        """Single-word name stays as-is, title-cased."""
        assert format_display_name("Marvin") == "Marvin"

    def test_three_words_abbreviates_middle(self) -> None:
        """Three-word name abbreviates the middle name."""
        assert format_display_name("Antonio Ismael Melo") == "Antonio I. Melo"

    def test_multiple_middles_all_abbreviated(self) -> None:
        """Multiple middle names are all abbreviated."""
        assert (
            format_display_name("Antonio Ismael Rodrigues Melo")
            == "Antonio I. R. Melo"
        )

    def test_particles_removed_de(self) -> None:
        """Particle 'de' is removed from name."""
        assert format_display_name("Antonio de Melo") == "Antonio Melo"

    def test_particles_removed_do(self) -> None:
        """Particle 'do' is removed."""
        assert format_display_name("João do Carmo") == "João Carmo"

    def test_particles_removed_dos(self) -> None:
        """Particle 'dos' is removed."""
        assert format_display_name("Maria dos Santos") == "Maria Santos"

    def test_particles_removed_da(self) -> None:
        """Particle 'da' is removed."""
        assert format_display_name("Ana da Silva") == "Ana Silva"

    def test_particles_removed_das(self) -> None:
        """Particle 'das' is removed."""
        assert format_display_name("Carlos das Neves") == "Carlos Neves"

    def test_particles_removed_di(self) -> None:
        """Particle 'di' is removed."""
        assert format_display_name("Paulo di Martino") == "Paulo Martino"

    def test_particles_removed_du(self) -> None:
        """Particle 'du' is removed."""
        assert format_display_name("Jean du Lac") == "Jean Lac"

    def test_complex_name_with_particles_and_middles(self) -> None:
        """Full name with particles and multiple middles."""
        assert (
            format_display_name("Antonio Ismael Rodrigues de Melo")
            == "Antonio I. R. Melo"
        )

    def test_particles_case_insensitive(self) -> None:
        """Particles are removed regardless of case."""
        assert format_display_name("Ana DA Silva") == "Ana Silva"
        assert format_display_name("João DOS Santos") == "João Santos"

    def test_multiple_particles(self) -> None:
        """Multiple particles in a single name are all removed."""
        assert (
            format_display_name("João dos Santos da Silva")
            == "João S. Silva"
        )

    def test_whitespace_trimming(self) -> None:
        """Leading/trailing whitespace is stripped."""
        assert format_display_name("  Rafa  ") == "Rafa"

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        assert format_display_name("") == ""

    def test_whitespace_only(self) -> None:
        """Whitespace-only string returns empty string."""
        assert format_display_name("   ") == ""

    def test_name_with_extra_spaces(self) -> None:
        """Name with extra internal spaces works correctly."""
        assert format_display_name("  ana  clara  ritter  ") == "Ana C. Ritter"

    def test_long_name(self) -> None:
        """Long multi-part name abbreviates middles, removes particles."""
        assert (
            format_display_name("Victor Manuel de guedes cavalcante")
            == "Victor M. G. Cavalcante"
        )

    def test_lowercase_name_becomes_title_case(self) -> None:
        """All-lowercase name becomes title case."""
        assert format_display_name("guilherme silva") == "Guilherme Silva"

    def test_uppercase_name_becomes_title_case(self) -> None:
        """All-uppercase name becomes title case."""
        assert format_display_name("GABRIEL MENDES") == "Gabriel Mendes"

    def test_mixed_case_normalized(self) -> None:
        """Mixed case is normalized to title case."""
        assert format_display_name("jOÃO pEDRO dINIZ") == "João P. Diniz"

    def test_name_only_particles_returns_empty(self) -> None:
        """Name consisting solely of particles returns empty string."""
        assert format_display_name("de do dos") == ""

    def test_name_with_pipe_character(self) -> None:
        """Name containing pipe character processes correctly."""
        result = format_display_name("Edson Damianni | Lançador 6 em 7")
        # '|', '6' etc. are treated as regular middle tokens and abbreviated
        assert result == "Edson D. |. L. 6. E. 7"

    def test_single_middle_abbreviated(self) -> None:
        """Single middle name is abbreviated."""
        assert format_display_name("João Pedro Diniz") == "João P. Diniz"

    def test_particle_between_middles(self) -> None:
        """Particle between middle names is filtered out."""
        assert (
            format_display_name("Maria Clara de Souza Lima")
            == "Maria C. S. Lima"
        )
