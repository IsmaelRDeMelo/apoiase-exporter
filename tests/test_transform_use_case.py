"""Tests for the TransformApoiadoresUseCase."""

from datetime import datetime
from pathlib import Path
from typing import Any

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


def _make_use_case(
    apoiadores: list[Apoiador],
) -> tuple[TransformApoiadoresUseCase, MockWriter, MockWriter]:
    """Helper to create a use case with mock reader/writers."""
    reader = MockReader(apoiadores)
    yaml_writer = MockWriter()
    json_writer = MockWriter()
    uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)
    return uc, yaml_writer, json_writer


def _make_csv_fixture(tmp_path: Path) -> Path:
    """Create a minimal CSV file for validation tests."""
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("header\nvalue", encoding="utf-8")
    return csv_path


class TestCSVValidation:
    """Tests for CSV file validation."""

    def test_missing_csv_raises_file_not_found(self, tmp_path: Path) -> None:
        """Raises FileNotFoundError when CSV does not exist."""
        uc, _, _ = _make_use_case([])
        missing = tmp_path / "does_not_exist.csv"

        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            uc.execute(missing, tmp_path, datetime(2026, 3, 14))

    def test_existing_csv_does_not_raise(self, tmp_path: Path) -> None:
        """No error when CSV exists."""
        csv_path = _make_csv_fixture(tmp_path)
        uc, _, _ = _make_use_case(
            [_make_apoiador(data_ultima_mudanca=datetime(2026, 3, 1))]
        )

        # Should not raise
        uc.execute(csv_path, tmp_path, datetime(2026, 3, 14))


class TestTransformUseCase:
    """Tests for the transformation use case."""

    def test_total_apoiadores_counts_active_only(self, tmp_path: Path) -> None:
        """total_apoiadores counts only 'Ativo' status."""
        csv_path = _make_csv_fixture(tmp_path)
        apoiadores = [
            _make_apoiador(status="Ativo", data_ultima_mudanca=datetime(2026, 3, 1)),
            _make_apoiador(status="Ativo", data_ultima_mudanca=datetime(2026, 3, 2)),
            _make_apoiador(status="Desativado", data_ultima_mudanca=datetime(2026, 3, 1)),
            _make_apoiador(status="Inadimplente", data_ultima_mudanca=datetime(2026, 3, 1)),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, datetime(2026, 3, 14))

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_apoiadores"] == 2

    def test_total_pendente_counts_aguardando(self, tmp_path: Path) -> None:
        """total_pendente counts 'Aguardando Confirmação' status."""
        csv_path = _make_csv_fixture(tmp_path)
        apoiadores = [
            _make_apoiador(
                status="Aguardando Confirmação",
                data_ultima_mudanca=datetime(2026, 3, 1),
            ),
            _make_apoiador(
                status="Aguardando Confirmação",
                data_ultima_mudanca=datetime(2026, 3, 2),
            ),
            _make_apoiador(status="Ativo", data_ultima_mudanca=datetime(2026, 3, 1)),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, datetime(2026, 3, 14))

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_pendente"] == 2

    def test_total_inadimplente(self, tmp_path: Path) -> None:
        """total_inadimplente counts 'Inadimplente' status."""
        csv_path = _make_csv_fixture(tmp_path)
        apoiadores = [
            _make_apoiador(
                status="Inadimplente",
                data_ultima_mudanca=datetime(2026, 3, 1),
            ),
            _make_apoiador(status="Ativo", data_ultima_mudanca=datetime(2026, 3, 1)),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, datetime(2026, 3, 14))

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_inadimplente"] == 1

    def test_total_recebido_mes_atual(self, tmp_path: Path) -> None:
        """Sums valor for active/pending in current month."""
        csv_path = _make_csv_fixture(tmp_path)
        ref = datetime(2026, 3, 14)
        apoiadores = [
            _make_apoiador(
                status="Ativo", valor=10.0, data_ultima_mudanca=datetime(2026, 3, 1)
            ),
            _make_apoiador(
                status="Aguardando Confirmação",
                valor=5.0,
                data_ultima_mudanca=datetime(2026, 3, 5),
            ),
            _make_apoiador(
                status="Ativo", valor=20.0, data_ultima_mudanca=datetime(2026, 2, 15)
            ),
            _make_apoiador(
                status="Desativado",
                valor=100.0,
                data_ultima_mudanca=datetime(2026, 3, 1),
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, ref)

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_recebido_mes_atual"] == 15.0

    def test_total_recebido_mes_anterior(self, tmp_path: Path) -> None:
        """Sums valor for active/pending in previous month."""
        csv_path = _make_csv_fixture(tmp_path)
        ref = datetime(2026, 3, 14)
        apoiadores = [
            _make_apoiador(
                status="Ativo", valor=20.0, data_ultima_mudanca=datetime(2026, 2, 15)
            ),
            _make_apoiador(
                status="Aguardando Confirmação",
                valor=15.0,
                data_ultima_mudanca=datetime(2026, 2, 1),
            ),
            _make_apoiador(
                status="Ativo", valor=10.0, data_ultima_mudanca=datetime(2026, 3, 1)
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, ref)

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_recebido_mes_anterior"] == 35.0

    def test_january_previous_month_is_december(self, tmp_path: Path) -> None:
        """When reference is January, previous month is December of prior year."""
        csv_path = _make_csv_fixture(tmp_path)
        ref = datetime(2026, 1, 15)
        apoiadores = [
            _make_apoiador(
                status="Ativo",
                valor=50.0,
                data_ultima_mudanca=datetime(2025, 12, 20),
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, ref)

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_recebido_mes_anterior"] == 50.0

    def test_recompensas_sorted_by_date_oldest_first(
        self, tmp_path: Path
    ) -> None:
        """Names are sorted by date (oldest first), not alphabetically."""
        csv_path = _make_csv_fixture(tmp_path)
        apoiadores = [
            _make_apoiador(
                nome="zoe silva",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 1, 10),  # oldest
            ),
            _make_apoiador(
                nome="alice santos",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 5),  # newest
            ),
            _make_apoiador(
                nome="BOB LIMA",
                status="Inadimplente",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 2, 15),
            ),
            _make_apoiador(
                nome="Carol Dias",
                status="Ativo",
                recompensa=18,
                data_ultima_mudanca=datetime(2026, 3, 1),
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, datetime(2026, 3, 14))

        recompensas = yaml_writer.written_data["apoia-se"]["recompensas"]

        assert "5-pesetas" in recompensas
        # Zoe is oldest (Jan 10), Alice is newest (Mar 5) → Zoe first
        assert (
            recompensas["5-pesetas"]["apoiadores_com_status_ativo"]
            == "Zoe Silva, Alice Santos"
        )
        assert (
            recompensas["5-pesetas"]["apoiadores_com_status_inadimplente"]
            == "Bob Lima"
        )

        assert "18-pesetas" in recompensas
        assert (
            recompensas["18-pesetas"]["apoiadores_com_status_ativo"]
            == "Carol Dias"
        )

    def test_none_dates_sorted_last(self, tmp_path: Path) -> None:
        """Supporters with None dates are placed at the end of the list."""
        csv_path = _make_csv_fixture(tmp_path)
        apoiadores = [
            _make_apoiador(
                nome="Alice",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=None,  # goes to end
            ),
            _make_apoiador(
                nome="Bob",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 1, 10),
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, datetime(2026, 3, 14))

        recompensas = yaml_writer.written_data["apoia-se"]["recompensas"]
        # Bob (Jan 10) first, Alice (None → last)
        assert (
            recompensas["5-pesetas"]["apoiadores_com_status_ativo"]
            == "Bob, Alice"
        )

    def test_metadata_json_output(self, tmp_path: Path) -> None:
        """JSON metadata contains id, nome, email for all supporters."""
        csv_path = _make_csv_fixture(tmp_path)
        apoiadores = [
            _make_apoiador(id="A1", nome="Rafa", email="rafa@test.com"),
            _make_apoiador(id="A2", nome="Rafa", email="rafa2@test.com"),
        ]
        uc, _, json_writer = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, datetime(2026, 3, 14))

        metadata = json_writer.written_data
        assert len(metadata) == 2
        assert metadata[0]["id"] == "A1"
        assert metadata[1]["email"] == "rafa2@test.com"

    def test_artifact_paths_use_date_serial(self, tmp_path: Path) -> None:
        """Generated artifact paths use date/serial format."""
        csv_path = _make_csv_fixture(tmp_path)
        uc, _, _ = _make_use_case(
            [_make_apoiador(data_ultima_mudanca=datetime(2026, 3, 1))]
        )
        ref = datetime(2026, 3, 14)

        yaml_path, json_path = uc.execute(csv_path, tmp_path, ref)

        assert "2026-03-14" in str(yaml_path)
        assert yaml_path.name == "001.yaml"
        assert json_path.name == "001.json"

    def test_serial_increments(self, tmp_path: Path) -> None:
        """Serial number increments with each run on the same date."""
        from src.infrastructure.yaml_writer import YAMLArtifactWriter
        from src.infrastructure.json_writer import JSONArtifactWriter

        csv_path = _make_csv_fixture(tmp_path)
        reader = MockReader(
            [_make_apoiador(data_ultima_mudanca=datetime(2026, 3, 1))]
        )
        yaml_writer = YAMLArtifactWriter()
        json_writer = JSONArtifactWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)
        ref = datetime(2026, 3, 14)

        yaml1, _ = uc.execute(csv_path, tmp_path, ref)
        yaml2, _ = uc.execute(csv_path, tmp_path, ref)

        assert yaml1.name == "001.yaml"
        assert yaml2.name == "002.yaml"

    def test_desativado_not_counted_in_standard_totals(
        self, tmp_path: Path
    ) -> None:
        """Desativado status is not counted in standard totals."""
        csv_path = _make_csv_fixture(tmp_path)
        apoiadores = [
            _make_apoiador(
                status="Desativado", data_ultima_mudanca=datetime(2026, 3, 1)
            ),
            _make_apoiador(
                status="Desativado", data_ultima_mudanca=datetime(2026, 3, 2)
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, datetime(2026, 3, 14))

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_apoiadores"] == 0
        assert result["apoia-se"]["total_pendente"] == 0
        assert result["apoia-se"]["total_inadimplente"] == 0

    def test_none_date_not_counted_in_monthly(self, tmp_path: Path) -> None:
        """Supporters with None date are not counted in monthly totals."""
        csv_path = _make_csv_fixture(tmp_path)
        apoiadores = [
            _make_apoiador(
                status="Ativo", valor=10.0, data_ultima_mudanca=None
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, datetime(2026, 3, 14))

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_recebido_mes_atual"] == 0.0
        assert result["apoia-se"]["total_recebido_mes_anterior"] == 0.0

    def test_empty_recompensa_fields_omitted(self, tmp_path: Path) -> None:
        """Empty status groups are omitted from recompensa output."""
        csv_path = _make_csv_fixture(tmp_path)
        apoiadores = [
            _make_apoiador(
                nome="Alice",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 1),
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, datetime(2026, 3, 14))

        recompensas = yaml_writer.written_data["apoia-se"]["recompensas"]
        assert "apoiadores_com_status_inadimplente" not in recompensas["5-pesetas"]
        assert "apoiadores_com_status_pendente" not in recompensas["5-pesetas"]

    def test_execute_without_reference_date(self, tmp_path: Path) -> None:
        """Execute without reference_date uses current date (doesn't crash)."""
        csv_path = _make_csv_fixture(tmp_path)
        uc, _, _ = _make_use_case(
            [_make_apoiador(data_ultima_mudanca=datetime(2026, 3, 1))]
        )

        yaml_path, json_path = uc.execute(csv_path, tmp_path)
        # Should produce files under today's date dir
        assert yaml_path.parent.name  # Has a date dir name

    def test_name_formatting_with_particles(self, tmp_path: Path) -> None:
        """Names with particles are formatted correctly in output."""
        csv_path = _make_csv_fixture(tmp_path)
        apoiadores = [
            _make_apoiador(
                nome="Antonio Ismael Rodrigues de Melo",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 1),
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, datetime(2026, 3, 14))

        recompensas = yaml_writer.written_data["apoia-se"]["recompensas"]
        assert (
            recompensas["5-pesetas"]["apoiadores_com_status_ativo"]
            == "Antonio I. R. Melo"
        )

    def test_name_formatting_abbreviated_middle(self, tmp_path: Path) -> None:
        """Names with middles are abbreviated in output."""
        csv_path = _make_csv_fixture(tmp_path)
        apoiadores = [
            _make_apoiador(
                nome="João Pedro Diniz",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 1),
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, datetime(2026, 3, 14))

        recompensas = yaml_writer.written_data["apoia-se"]["recompensas"]
        assert (
            recompensas["5-pesetas"]["apoiadores_com_status_ativo"]
            == "João P. Diniz"
        )


class TestActiveRecent:
    """Tests for the 'Apoiadores Ativos Últimos N Dias' feature."""

    def test_ativos_recentes_includes_all_statuses_within_period(
        self, tmp_path: Path
    ) -> None:
        """Ativo always included; other statuses only within N days."""
        csv_path = _make_csv_fixture(tmp_path)
        ref = datetime(2026, 3, 14)
        apoiadores = [
            _make_apoiador(
                nome="Ativo Recent",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 1),  # 13 days ago
            ),
            _make_apoiador(
                nome="Desativado Recent",
                status="Desativado",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 10),  # 4 days ago
            ),
            _make_apoiador(
                nome="Inadimplente Recent",
                status="Inadimplente",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 5),  # 9 days ago
            ),
            _make_apoiador(
                nome="Old Supporter",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2025, 12, 1),  # > 30 days ago, but Ativo = always in
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, ref, days_filter=30)

        result = yaml_writer.written_data
        # All 4: Ativo always included regardless of date, other 2 within period
        assert result["apoia-se"]["total_ativos_recentes"] == 4

        recompensas = result["apoia-se"]["recompensas"]
        recent_names = recompensas["5-pesetas"][
            "apoiadores_ativos_ultimos_n_dias"
        ]
        assert "Ativo Recent" in recent_names
        assert "Desativado Recent" in recent_names
        assert "Inadimplente Recent" in recent_names
        assert "Old Supporter" in recent_names  # Ativo = always included

    def test_ativos_recentes_respects_days_filter(
        self, tmp_path: Path
    ) -> None:
        """Ativo is always included regardless of days_filter."""
        csv_path = _make_csv_fixture(tmp_path)
        ref = datetime(2026, 3, 14)
        apoiadores = [
            _make_apoiador(
                nome="Very Recent",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 10),  # 4 days ago
            ),
            _make_apoiador(
                nome="Semi Recent",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 1),  # 13 days ago, but Ativo = always in
            ),
            _make_apoiador(
                nome="Old Desativado",
                status="Desativado",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 1),  # 13 days ago -> outside 10-day window
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, ref, days_filter=10)

        result = yaml_writer.written_data
        # Both Ativo included; Desativado outside window excluded
        assert result["apoia-se"]["total_ativos_recentes"] == 2
        assert result["apoia-se"]["dias_filtro"] == 10

    def test_ativos_recentes_15_days_filter(self, tmp_path: Path) -> None:
        """Ativo always included; non-Ativo uses 15-day filter."""
        csv_path = _make_csv_fixture(tmp_path)
        ref = datetime(2026, 3, 14)
        apoiadores = [
            _make_apoiador(
                nome="Recent",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 5),  # 9 days ago
            ),
            _make_apoiador(
                nome="Old Ativo",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 2, 20),  # 22 days ago, still included
            ),
            _make_apoiador(
                nome="Old Desativado",
                status="Desativado",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 2, 20),  # 22 days ago, excluded
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, ref, days_filter=15)

        result = yaml_writer.written_data
        # Both Ativo included; Desativado at 22 days excluded by 15-day window
        assert result["apoia-se"]["total_ativos_recentes"] == 2

    def test_ativos_recentes_60_days_filter(self, tmp_path: Path) -> None:
        """Ativo always included; Desativado uses 60-day filter."""
        csv_path = _make_csv_fixture(tmp_path)
        ref = datetime(2026, 3, 14)
        apoiadores = [
            _make_apoiador(
                nome="Recent",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 5),
            ),
            _make_apoiador(
                nome="Old Ativo",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2025, 12, 1),  # 103 days ago, still included
            ),
            _make_apoiador(
                nome="Desativado Within 60",
                status="Desativado",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 2, 1),  # 41 days ago, within 60d
            ),
            _make_apoiador(
                nome="Desativado Outside 60",
                status="Desativado",
                recompensa=5,
                data_ultima_mudanca=datetime(2025, 12, 1),  # 103 days ago, excluded
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, ref, days_filter=60)

        result = yaml_writer.written_data
        # 2 Ativo (always) + 1 Desativado within 60d = 3; last Desativado excluded
        assert result["apoia-se"]["total_ativos_recentes"] == 3

    def test_ativos_recentes_ativo_none_date_included(self, tmp_path: Path) -> None:
        """Ativo with None date is included (Ativo is always in active recent)."""
        csv_path = _make_csv_fixture(tmp_path)
        ref = datetime(2026, 3, 14)
        apoiadores = [
            _make_apoiador(
                nome="No Date Ativo",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=None,
            ),
            _make_apoiador(
                nome="No Date Desativado",
                status="Desativado",
                recompensa=5,
                data_ultima_mudanca=None,
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, ref)

        result = yaml_writer.written_data
        # Ativo with None date is included; Desativado with None date is not
        assert result["apoia-se"]["total_ativos_recentes"] == 1

    def test_ativos_recentes_sorted_by_date(self, tmp_path: Path) -> None:
        """Active recent names are sorted by date (oldest first)."""
        csv_path = _make_csv_fixture(tmp_path)
        ref = datetime(2026, 3, 14)
        apoiadores = [
            _make_apoiador(
                nome="Charlie",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 10),  # newest
            ),
            _make_apoiador(
                nome="Alice",
                status="Ativo",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 2, 20),  # oldest
            ),
            _make_apoiador(
                nome="Bob",
                status="Desativado",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 1),  # middle
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, ref)

        recompensas = yaml_writer.written_data["apoia-se"]["recompensas"]
        recent = recompensas["5-pesetas"]["apoiadores_ativos_ultimos_n_dias"]
        assert recent == "Alice, Bob, Charlie"

    def test_dias_filtro_in_output(self, tmp_path: Path) -> None:
        """days_filter value is present in YAML output."""
        csv_path = _make_csv_fixture(tmp_path)
        uc, yaml_writer, _ = _make_use_case(
            [_make_apoiador(data_ultima_mudanca=datetime(2026, 3, 1))]
        )
        uc.execute(csv_path, tmp_path, datetime(2026, 3, 14), days_filter=45)

        result = yaml_writer.written_data
        assert result["apoia-se"]["dias_filtro"] == 45

    def test_aguardando_within_period_included(self, tmp_path: Path) -> None:
        """Aguardando Confirmação within N days is included in active recent."""
        csv_path = _make_csv_fixture(tmp_path)
        ref = datetime(2026, 3, 14)
        apoiadores = [
            _make_apoiador(
                nome="Pending Guy",
                status="Aguardando Confirmação",
                recompensa=5,
                data_ultima_mudanca=datetime(2026, 3, 5),
            ),
        ]
        uc, yaml_writer, _ = _make_use_case(apoiadores)
        uc.execute(csv_path, tmp_path, ref)

        result = yaml_writer.written_data
        assert result["apoia-se"]["total_ativos_recentes"] == 1


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


class TestNextSerial:
    """Tests for the serial number logic."""

    def test_empty_dir_returns_1(self, tmp_path: Path) -> None:
        """Empty directory starts at serial 1."""
        assert TransformApoiadoresUseCase._next_serial(tmp_path) == 1

    def test_existing_files_increment(self, tmp_path: Path) -> None:
        """Returns max existing serial + 1."""
        (tmp_path / "001.yaml").touch()
        (tmp_path / "002.yaml").touch()
        assert TransformApoiadoresUseCase._next_serial(tmp_path) == 3

    def test_non_numeric_files_ignored(self, tmp_path: Path) -> None:
        """Non-numeric YAML files are ignored."""
        (tmp_path / "001.yaml").touch()
        (tmp_path / "readme.yaml").touch()
        assert TransformApoiadoresUseCase._next_serial(tmp_path) == 2
