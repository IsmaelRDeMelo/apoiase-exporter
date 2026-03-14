"""Tests for the YAML artifact writer adapter."""

from pathlib import Path

import yaml

from src.infrastructure.yaml_writer import YAMLArtifactWriter


class TestYAMLArtifactWriter:
    """Tests for the YAMLArtifactWriter adapter."""

    def test_write_creates_file(self, tmp_path: Path) -> None:
        """Writer creates the output file."""
        writer = YAMLArtifactWriter()
        output = tmp_path / "test.yaml"
        data = {"key": "value"}

        writer.write(data, output)

        assert output.exists()

    def test_write_valid_yaml(self, tmp_path: Path) -> None:
        """Writer produces valid YAML."""
        writer = YAMLArtifactWriter()
        output = tmp_path / "test.yaml"
        data = {"apoia-se": {"total_apoiadores": 5}}

        writer.write(data, output)

        with open(output, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
        assert loaded["apoia-se"]["total_apoiadores"] == 5

    def test_write_preserves_unicode(self, tmp_path: Path) -> None:
        """Writer preserves Unicode characters."""
        writer = YAMLArtifactWriter()
        output = tmp_path / "test.yaml"
        data = {"nome": "João Gonçalves"}

        writer.write(data, output)

        with open(output, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
        assert loaded["nome"] == "João Gonçalves"

    def test_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Writer creates parent directories if they don't exist."""
        writer = YAMLArtifactWriter()
        output = tmp_path / "sub" / "dir" / "test.yaml"

        writer.write({"key": "value"}, output)

        assert output.exists()

    def test_write_nested_structure(self, tmp_path: Path) -> None:
        """Writer correctly serializes nested structures."""
        writer = YAMLArtifactWriter()
        output = tmp_path / "test.yaml"
        data = {
            "apoia-se": {
                "total_apoiadores": 10,
                "recompensas": {
                    5: {"apoiadores_com_status_ativo": "Alice, Bob"},
                },
            }
        }

        writer.write(data, output)

        with open(output, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
        assert loaded["apoia-se"]["recompensas"][5]["apoiadores_com_status_ativo"] == "Alice, Bob"
