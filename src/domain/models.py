"""Domain models for the Apoia-se ETL pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


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
    """Groups supporters by status within a reward tier."""

    apoiadores_com_status_ativo: str = ""
    apoiadores_com_status_pendente: str = ""
    apoiadores_com_status_inadimplente: str = ""
    apoiadores_com_status_aguardando_confirmacao: str = ""
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
    recompensas: dict[int, RecompensaGroup] = field(default_factory=dict)
