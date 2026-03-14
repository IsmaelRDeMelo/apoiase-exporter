"""Tests for the TransformApoiadoresUseCase."""

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.application.transform_use_case import TransformApoiadoresUseCase
from src.domain.models import Apoiador
from src.domain.ports import ArtifactWriterPort, DataReaderPort


def _make_apoiador(
    id: str = "AAA",
    nome: str = "Test User",
    email: str = "test@test.com",
    valor: float = 10.0,
    recompensa: int = 5,
    apoios_efetuados: int = 1,
    total_apoiado: float = 10.0,
    status: str = "Ativo",
    data_ultima_mudanca: datetime | None = None,
) -> Apoiador:
    """Helper to create Apoiador with defaults."""
    return Apoiador(
        id=id,
        nome=nome,
        email=email,
        valor=valor,
        recompensa=recompensa,
        apoios_efetuados=apoios_efetuados,
        total_apoiado=total_apoiado,
        status=status,
        data_ultima_mudanca=data_ultima_mudanca,
    )


class MockReader(DataReaderPort):
    """Mock reader that returns a fixed list of apoiadores."""

    def __init__(self, apoiadores: list[Apoiador]) -> None:
        self._apoiadores = apoiadores

    def read(self, path: Path) -> list[Apoiador]:
        return self._apoiadores


class MockWriter(ArtifactWriterPort):
    """Mock writer that captures written data."""

    def __init__(self) -> None:
        self.written_data: Any = None
        self.written_path: Path | None = None

    def write(self, data: Any, path: Path) -> None:
        self.written_data = data
        self.written_path = path


class TestTransformUseCase:
    """Tests for the transformation use case."""

    def test_total_apoiadores_counts_active_only(self, tmp_path: Path) -> None:
        """total_apoiadores counts only 'Ativo' status."""
        apoiadores = [
            _make_apoiador(status="Ativo"),
            _make_apoiador(status="Ativo"),
            _make_apoiador(status="Desativado"),
            _make_apoiador(status="Inadimplente"),
        ]
        reader = MockReader(apoiadores)
        yaml_writer = MockWriter()
        json_writer = MockWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        uc.execute(Path("fake.csv"), tmp_path, datetime(2026, 3, 14))

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_apoiadores"] == 2

    def test_total_pendente_counts_aguardando(self, tmp_path: Path) -> None:
        """total_pendente counts 'Aguardando Confirmação' status."""
        apoiadores = [
            _make_apoiador(status="Aguardando Confirmação"),
            _make_apoiador(status="Aguardando Confirmação"),
            _make_apoiador(status="Ativo"),
        ]
        reader = MockReader(apoiadores)
        yaml_writer = MockWriter()
        json_writer = MockWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        uc.execute(Path("fake.csv"), tmp_path, datetime(2026, 3, 14))

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_pendente"] == 2

    def test_total_inadimplente(self, tmp_path: Path) -> None:
        """total_inadimplente counts 'Inadimplente' status."""
        apoiadores = [
            _make_apoiador(status="Inadimplente"),
            _make_apoiador(status="Ativo"),
        ]
        reader = MockReader(apoiadores)
        yaml_writer = MockWriter()
        json_writer = MockWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        uc.execute(Path("fake.csv"), tmp_path, datetime(2026, 3, 14))

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_inadimplente"] == 1

    def test_total_recebido_mes_atual(self, tmp_path: Path) -> None:
        """Sums valor for active/pending in current month."""
        ref = datetime(2026, 3, 14)
        apoiadores = [
            _make_apoiador(
                status="Ativo",
                valor=10.0,
                data_ultima_mudanca=datetime(2026, 3, 1),
            ),
            _make_apoiador(
                status="Aguardando Confirmação",
                valor=5.0,
                data_ultima_mudanca=datetime(2026, 3, 5),
            ),
            _make_apoiador(
                status="Ativo",
                valor=20.0,
                data_ultima_mudanca=datetime(2026, 2, 15),
            ),
            _make_apoiador(
                status="Desativado",
                valor=100.0,
                data_ultima_mudanca=datetime(2026, 3, 1),
            ),
        ]
        reader = MockReader(apoiadores)
        yaml_writer = MockWriter()
        json_writer = MockWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        uc.execute(Path("fake.csv"), tmp_path, ref)

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_recebido_mes_atual"] == 15.0

    def test_total_recebido_mes_anterior(self, tmp_path: Path) -> None:
        """Sums valor for active/pending in previous month."""
        ref = datetime(2026, 3, 14)
        apoiadores = [
            _make_apoiador(
                status="Ativo",
                valor=20.0,
                data_ultima_mudanca=datetime(2026, 2, 15),
            ),
            _make_apoiador(
                status="Aguardando Confirmação",
                valor=15.0,
                data_ultima_mudanca=datetime(2026, 2, 1),
            ),
            _make_apoiador(
                status="Ativo",
                valor=10.0,
                data_ultima_mudanca=datetime(2026, 3, 1),
            ),
        ]
        reader = MockReader(apoiadores)
        yaml_writer = MockWriter()
        json_writer = MockWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        uc.execute(Path("fake.csv"), tmp_path, ref)

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_recebido_mes_anterior"] == 35.0

    def test_january_previous_month_is_december(self, tmp_path: Path) -> None:
        """When reference is January, previous month is December of prior year."""
        ref = datetime(2026, 1, 15)
        apoiadores = [
            _make_apoiador(
                status="Ativo",
                valor=50.0,
                data_ultima_mudanca=datetime(2025, 12, 20),
            ),
        ]
        reader = MockReader(apoiadores)
        yaml_writer = MockWriter()
        json_writer = MockWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        uc.execute(Path("fake.csv"), tmp_path, ref)

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_recebido_mes_anterior"] == 50.0

    def test_recompensas_grouping(self, tmp_path: Path) -> None:
        """Groups supporters by recompensa and status with sorted names."""
        apoiadores = [
            _make_apoiador(nome="Zoe Silva", status="Ativo", recompensa=5),
            _make_apoiador(nome="Alice Santos", status="Ativo", recompensa=5),
            _make_apoiador(nome="Bob Lima", status="Inadimplente", recompensa=5),
            _make_apoiador(nome="Carol Dias", status="Ativo", recompensa=18),
        ]
        reader = MockReader(apoiadores)
        yaml_writer = MockWriter()
        json_writer = MockWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        uc.execute(Path("fake.csv"), tmp_path, datetime(2026, 3, 14))

        recompensas = yaml_writer.written_data["apoia-se"]["recompensas"]

        assert 5 in recompensas
        assert recompensas[5]["apoiadores_com_status_ativo"] == "Alice Santos, Zoe Silva"
        assert recompensas[5]["apoiadores_com_status_inadimplente"] == "Bob Lima"

        assert 18 in recompensas
        assert recompensas[18]["apoiadores_com_status_ativo"] == "Carol Dias"

    def test_metadata_json_output(self, tmp_path: Path) -> None:
        """JSON metadata contains id, nome, email for all supporters."""
        apoiadores = [
            _make_apoiador(id="A1", nome="Rafa", email="rafa@test.com"),
            _make_apoiador(id="A2", nome="Rafa", email="rafa2@test.com"),
        ]
        reader = MockReader(apoiadores)
        yaml_writer = MockWriter()
        json_writer = MockWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        uc.execute(Path("fake.csv"), tmp_path, datetime(2026, 3, 14))

        metadata = json_writer.written_data
        assert len(metadata) == 2
        assert metadata[0]["id"] == "A1"
        assert metadata[0]["nome"] == "Rafa"
        assert metadata[0]["email"] == "rafa@test.com"
        assert metadata[1]["id"] == "A2"
        assert metadata[1]["email"] == "rafa2@test.com"

    def test_artifact_paths_contain_uuid(self, tmp_path: Path) -> None:
        """Generated artifact paths use UUID filenames."""
        reader = MockReader([_make_apoiador()])
        yaml_writer = MockWriter()
        json_writer = MockWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        yaml_path, json_path = uc.execute(
            Path("fake.csv"), tmp_path, datetime(2026, 3, 14)
        )

        assert yaml_path.suffix == ".yaml"
        assert json_path.suffix == ".json"
        assert yaml_path.stem == json_path.stem  # Same UUID

    def test_desativado_not_counted(self, tmp_path: Path) -> None:
        """Desativado status is not counted in any total."""
        apoiadores = [
            _make_apoiador(status="Desativado"),
            _make_apoiador(status="Desativado"),
        ]
        reader = MockReader(apoiadores)
        yaml_writer = MockWriter()
        json_writer = MockWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        uc.execute(Path("fake.csv"), tmp_path, datetime(2026, 3, 14))

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_apoiadores"] == 0
        assert result["apoia-se"]["total_pendente"] == 0
        assert result["apoia-se"]["total_inadimplente"] == 0

    def test_none_date_not_counted_in_monthly(self, tmp_path: Path) -> None:
        """Supporters with None date are not counted in monthly totals."""
        apoiadores = [
            _make_apoiador(
                status="Ativo",
                valor=10.0,
                data_ultima_mudanca=None,
            ),
        ]
        reader = MockReader(apoiadores)
        yaml_writer = MockWriter()
        json_writer = MockWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        uc.execute(Path("fake.csv"), tmp_path, datetime(2026, 3, 14))

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_recebido_mes_atual"] == 0.0
        assert result["apoia-se"]["total_recebido_mes_anterior"] == 0.0

    def test_empty_recompensa_fields_omitted(self, tmp_path: Path) -> None:
        """Empty status groups are omitted from recompensa output."""
        apoiadores = [
            _make_apoiador(nome="Alice", status="Ativo", recompensa=5),
        ]
        reader = MockReader(apoiadores)
        yaml_writer = MockWriter()
        json_writer = MockWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        uc.execute(Path("fake.csv"), tmp_path, datetime(2026, 3, 14))

        recompensas = yaml_writer.written_data["apoia-se"]["recompensas"]
        assert "apoiadores_com_status_inadimplente" not in recompensas[5]
        assert "apoiadores_com_status_pendente" not in recompensas[5]

    def test_execute_without_reference_date(self, tmp_path: Path) -> None:
        """Execute without reference_date uses current date (doesn't crash)."""
        reader = MockReader([_make_apoiador()])
        yaml_writer = MockWriter()
        json_writer = MockWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        yaml_path, json_path = uc.execute(Path("fake.csv"), tmp_path)

        assert yaml_path.exists() is False  # MockWriter doesn't write to disk
        assert json_path.exists() is False


class TestStatusToKey:
    """Tests for the status-to-key mapping."""

    def test_ativo(self) -> None:
        assert (
            TransformApoiadoresUseCase._status_to_key("Ativo")
            == "apoiadores_com_status_ativo"
        )

    def test_aguardando(self) -> None:
        assert (
            TransformApoiadoresUseCase._status_to_key("Aguardando Confirmação")
            == "apoiadores_com_status_pendente"
        )

    def test_inadimplente(self) -> None:
        assert (
            TransformApoiadoresUseCase._status_to_key("Inadimplente")
            == "apoiadores_com_status_inadimplente"
        )

    def test_unknown_returns_none(self) -> None:
        assert TransformApoiadoresUseCase._status_to_key("Desativado") is None

    def test_empty_returns_none(self) -> None:
        assert TransformApoiadoresUseCase._status_to_key("") is None
