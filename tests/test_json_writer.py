"""Tests for the JSON metadata artifact writer adapter."""

import json
from pathlib import Path

from src.infrastructure.json_writer import JSONArtifactWriter


class TestJSONArtifactWriter:
    """Tests for the JSONArtifactWriter adapter."""

    def test_write_creates_file(self, tmp_path: Path) -> None:
        """Writer creates the output file."""
        writer = JSONArtifactWriter()
        output = tmp_path / "test.json"

        writer.write([{"id": "A1"}], output)

        assert output.exists()

    def test_write_valid_json(self, tmp_path: Path) -> None:
        """Writer produces valid JSON."""
        writer = JSONArtifactWriter()
        output = tmp_path / "test.json"
        data = [{"id": "A1", "nome": "Test", "email": "test@test.com"}]

        writer.write(data, output)

        with open(output, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert len(loaded) == 1
        assert loaded[0]["id"] == "A1"

    def test_write_preserves_unicode(self, tmp_path: Path) -> None:
        """Writer preserves Unicode characters without escaping."""
        writer = JSONArtifactWriter()
        output = tmp_path / "test.json"
        data = [{"nome": "João Gonçalves"}]

        writer.write(data, output)

        content = output.read_text(encoding="utf-8")
        assert "João Gonçalves" in content
        # Ensure no ASCII escaping
        assert "\\u" not in content

    def test_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Writer creates parent directories if they don't exist."""
        writer = JSONArtifactWriter()
        output = tmp_path / "sub" / "dir" / "test.json"

        writer.write({"key": "value"}, output)

        assert output.exists()

    def test_write_indented(self, tmp_path: Path) -> None:
        """Writer produces indented JSON for readability."""
        writer = JSONArtifactWriter()
        output = tmp_path / "test.json"

        writer.write([{"id": "A1"}], output)

        content = output.read_text(encoding="utf-8")
        assert "\n" in content  # Indented output has newlines
