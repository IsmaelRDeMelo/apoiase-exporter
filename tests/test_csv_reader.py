"""Tests for the Polars CSV reader adapter."""

from pathlib import Path

import pytest

from src.infrastructure.csv_reader import PolarsCSVReader


@pytest.fixture
def csv_fixture(tmp_path: Path) -> Path:
    """Create a small CSV fixture file."""
    csv_content = (
        '"ID","Apoiador","Email","Valor","Recompensa","Apoios Efetuados",'
        '"Total Apoiado","Tipo","Status da Promessa","Visibilidade",'
        '"Data da Última Mudança no Status da Promessa","CEP","Rua","Número",'
        '"Complementos","Bairro","Cidade","UF","País","Endereço Completo"\n'
        '"ABC123","Fabio Akita","fabio@example.com",10,5,3,30,'
        '"Cartão de crédito","Ativo","Público","2026-03-01 08:51",'
        '"01000000","Rua A","1","","Centro","SP","SP","Brasil","Rua A, 1"\n'
        '"DEF456","Marvin","marvin@example.com",20,18,5,100,'
        '"Cartão de crédito","Desativado","Público","2025-12-15 10:00",'
        ',,,,,,,,\n'
        '"GHI789","Rafa Oliveira","rafa@example.com",15,5,2,30,'
        '"Boleto","Inadimplente","Público","",'
        ',,,,,,,,\n'
    )
    csv_path = tmp_path / "test.csv"
    csv_path.write_text(csv_content, encoding="utf-8")
    return csv_path


class TestPolarsCSVReader:
    """Tests for the PolarsCSVReader adapter."""

    def test_read_returns_list(self, csv_fixture: Path) -> None:
        """Reader returns a list of Apoiador objects."""
        reader = PolarsCSVReader()
        result = reader.read(csv_fixture)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_first_record_values(self, csv_fixture: Path) -> None:
        """First record values are correctly parsed."""
        reader = PolarsCSVReader()
        result = reader.read(csv_fixture)
        ap = result[0]
        assert ap.id == "ABC123"
        assert ap.nome == "Fabio Akita"
        assert ap.email == "fabio@example.com"
        assert ap.valor == 10.0
        assert ap.recompensa == 5
        assert ap.apoios_efetuados == 3
        assert ap.total_apoiado == 30.0
        assert ap.status == "Ativo"
        assert ap.data_ultima_mudanca is not None
        assert ap.data_ultima_mudanca.year == 2026
        assert ap.data_ultima_mudanca.month == 3

    def test_empty_date_parsed_as_none(self, csv_fixture: Path) -> None:
        """Empty date strings should be parsed as None."""
        reader = PolarsCSVReader()
        result = reader.read(csv_fixture)
        ap = result[2]  # GHI789 has empty date
        assert ap.data_ultima_mudanca is None

    def test_different_statuses(self, csv_fixture: Path) -> None:
        """Different statuses are correctly preserved."""
        reader = PolarsCSVReader()
        result = reader.read(csv_fixture)
        assert result[0].status == "Ativo"
        assert result[1].status == "Desativado"
        assert result[2].status == "Inadimplente"

    def test_numeric_values_as_floats(self, csv_fixture: Path) -> None:
        """Valor and Total Apoiado are parsed as floats."""
        reader = PolarsCSVReader()
        result = reader.read(csv_fixture)
        assert isinstance(result[0].valor, float)
        assert isinstance(result[0].total_apoiado, float)
        assert result[1].valor == 20.0
