"""Domain models for the Apoia-se ETL pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# Recompensa tier threshold: 0–59 = baixo, 60+ = premium
TIER_PREMIUM_THRESHOLD = 60


@dataclass(frozen=True)
class Apoiador:
    """Represents a single supporter from the Apoia-se platform."""

    id: str
    nome: str
    email: str
    valor: float
    recompensa: int
    apoios_efetuados: int
    total_apoiado: float
    status: str
    data_ultima_mudanca: Optional[datetime]


@dataclass
class RecompensaGroup:
    """Groups supporters by status within a unified reward tier."""

    nomes_unicos: str = ""
    apoiadores_com_status_ativo: str = ""
    apoiadores_com_outros_status: str = ""
    apoiadores_ativos_ultimos_n_dias: str = ""


@dataclass
class ApoiaSummary:
    """Aggregated summary of the Apoia-se supporter data."""

    total_apoiadores: int = 0
    total_pendente: int = 0
    total_inadimplente: int = 0
    total_recebido_mes_atual: float = 0.0
    total_recebido_mes_anterior: float = 0.0
    total_ativos_recentes: int = 0
    dias_filtro: int = 30

    # Two unified tiers replacing per-value buckets
    tier_baixo: RecompensaGroup = field(default_factory=RecompensaGroup)   # 0–59
    tier_premium: RecompensaGroup = field(default_factory=RecompensaGroup)  # 60+

    # Summary section
    sumario_ativos: str = ""           # unique active names from both tiers
    sumario_ativos_recentes: str = ""  # unique recently-active names from both tiers
    sumario_lista_completa: str = ""   # union(ativos + ativos_recentes), deduplicated
