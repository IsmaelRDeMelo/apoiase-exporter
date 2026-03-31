"""Tests for domain models."""

from datetime import datetime

from src.domain.models import ApoiaSummary, Apoiador, RecompensaGroup


class TestApoiador:
    """Tests for the Apoiador dataclass."""

    def test_create_apoiador(self) -> None:
        """Test creating a valid Apoiador instance."""
        apoiador = Apoiador(
            id="ABC123",
            nome="Fabio Akita",
            email="fabio@example.com",
            valor=10.0,
            recompensa=5,
            apoios_efetuados=3,
            total_apoiado=30.0,
            status="Ativo",
            data_ultima_mudanca=datetime(2026, 3, 1, 8, 51),
        )
        assert apoiador.id == "ABC123"
        assert apoiador.nome == "Fabio Akita"
        assert apoiador.email == "fabio@example.com"
        assert apoiador.valor == 10.0
        assert apoiador.recompensa == 5
        assert apoiador.apoios_efetuados == 3
        assert apoiador.total_apoiado == 30.0
        assert apoiador.status == "Ativo"
        assert apoiador.data_ultima_mudanca == datetime(2026, 3, 1, 8, 51)

    def test_apoiador_with_none_date(self) -> None:
        """Test creating Apoiador with None date."""
        apoiador = Apoiador(
            id="DEF456",
            nome="Marvin",
            email="marvin@example.com",
            valor=5.0,
            recompensa=5,
            apoios_efetuados=1,
            total_apoiado=5.0,
            status="Desativado",
            data_ultima_mudanca=None,
        )
        assert apoiador.data_ultima_mudanca is None

    def test_apoiador_is_frozen(self) -> None:
        """Test that Apoiador is immutable."""
        apoiador = Apoiador(
            id="ABC123",
            nome="Test",
            email="t@t.com",
            valor=5.0,
            recompensa=5,
            apoios_efetuados=1,
            total_apoiado=5.0,
            status="Ativo",
            data_ultima_mudanca=None,
        )
        try:
            apoiador.nome = "Changed"  # type: ignore
            assert False, "Should have raised FrozenInstanceError"
        except AttributeError:
            pass


class TestRecompensaGroup:
    """Tests for the RecompensaGroup dataclass."""

    def test_default_values(self) -> None:
        """Test that default values are empty strings."""
        group = RecompensaGroup()
        assert group.nomes_unicos == ""
        assert group.apoiadores_com_status_ativo == ""
        assert group.apoiadores_com_outros_status == ""
        assert group.apoiadores_ativos_ultimos_n_dias == ""

    def test_custom_values(self) -> None:
        """Test creating group with custom values."""
        group = RecompensaGroup(
            apoiadores_com_status_ativo="Alice, Bob",
            apoiadores_com_outros_status="Charlie",
        )
        assert group.apoiadores_com_status_ativo == "Alice, Bob"
        assert group.apoiadores_com_outros_status == "Charlie"

    def test_active_recent_field(self) -> None:
        """Test the active-recent field."""
        group = RecompensaGroup(
            apoiadores_ativos_ultimos_n_dias="Fabio Akita, Marvin",
        )
        assert group.apoiadores_ativos_ultimos_n_dias == "Fabio Akita, Marvin"


class TestApoiaSummary:
    """Tests for the ApoiaSummary dataclass."""

    def test_default_values(self) -> None:
        """Test that default values are zeros and empty fields."""
        summary = ApoiaSummary()
        assert summary.total_apoiadores == 0
        assert summary.total_pendente == 0
        assert summary.total_inadimplente == 0
        assert summary.total_recebido_mes_atual == 0.0
        assert summary.total_recebido_mes_anterior == 0.0
        assert summary.total_ativos_recentes == 0
        assert summary.dias_filtro == 30
        assert summary.sumario_ativos == ""
        assert summary.sumario_ativos_recentes == ""
        assert summary.sumario_lista_completa == ""

    def test_tier_baixo_default(self) -> None:
        """Test that tier_baixo defaults to an empty RecompensaGroup."""
        summary = ApoiaSummary()
        assert isinstance(summary.tier_baixo, RecompensaGroup)
        assert summary.tier_baixo.nomes_unicos == ""

    def test_tier_premium_default(self) -> None:
        """Test that tier_premium defaults to an empty RecompensaGroup."""
        summary = ApoiaSummary()
        assert isinstance(summary.tier_premium, RecompensaGroup)
        assert summary.tier_premium.apoiadores_com_status_ativo == ""

    def test_with_tiers(self) -> None:
        """Test summary with tier groups set."""
        group = RecompensaGroup(apoiadores_com_status_ativo="Fabio Akita")
        summary = ApoiaSummary(
            total_apoiadores=1,
            tier_baixo=group,
        )
        assert summary.total_apoiadores == 1
        assert summary.tier_baixo.apoiadores_com_status_ativo == "Fabio Akita"

    def test_custom_days_filter(self) -> None:
        """Test summary with custom days filter."""
        summary = ApoiaSummary(dias_filtro=15)
        assert summary.dias_filtro == 15

    def test_active_recent_count(self) -> None:
        """Test setting active recent count."""
        summary = ApoiaSummary(total_ativos_recentes=42)
        assert summary.total_ativos_recentes == 42
