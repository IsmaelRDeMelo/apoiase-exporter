# Apoia-se ETL Automation - PLAN

## Overview

Transform the supporter CSV extract from Apoia-se (`data/base-apoiadores-mf.csv`) into:
1. A **YAML summary** with aggregated metrics (active supporters, totals by status, rewards breakdown)
2. A **JSON metadata** file for debugging (maps names to IDs/emails for disambiguation)

Both artifacts are saved to `artifacts/<uuid>.yaml` and `artifacts/<uuid>.json`.

## Tech Stack

- **Python 3.12+** with venv
- **Polars** for CSV processing
- **PyYAML** for YAML output
- **pytest + pytest-cov** for testing (target ≥ 90% coverage)

## Architecture (Hexagonal)

```
src/
├── domain/           # Business logic, models, ports
│   ├── models.py     # Apoiador, RecompensaGroup, ApoiaSummary
│   ├── ports.py      # DataReaderPort, ArtifactWriterPort (ABCs)
│   └── name_utils.py # Short name extraction
├── application/      # Use cases
│   └── transform_use_case.py
├── infrastructure/   # Adapters
│   ├── csv_reader.py # PolarsCSVReader
│   ├── yaml_writer.py
│   └── json_writer.py
main.py               # Entry point, dependency wiring
tests/                # Unit + integration tests
```

## Business Rules

| Output Field | Calculation |
|---|---|
| `total_apoiadores` | Count where `Status da Promessa` == `"Ativo"` |
| `total_pendente` | Count where `Status da Promessa` == `"Aguardando Confirmação"` |
| `total_inadimplente` | Count where `Status da Promessa` == `"Inadimplente"` |
| `total_recebido_mes_atual` | Sum of `Valor` where status ∈ {Ativo, Aguardando Confirmação} AND date is current month |
| `total_recebido_mes_anterior` | Sum of `Valor` where status ∈ {Ativo, Aguardando Confirmação} AND date is previous month |
| `recompensas.<tier>` | Lists of short names (first + last) per status, comma-separated, alphabetically sorted |

## Name Extraction

- Multi-word: use first and last → `"Fabio Akita"` from `"Fabio Akita"`
- Single-word: keep as-is → `"Marvin"` from `"Marvin"`
- Strips leading/trailing whitespace

## JSON Metadata (Debug)

Maps each supporter with `id`, `nome`, `email` so duplicates with the same first name can be disambiguated.

## Test Plan

| Test File | Scope |
|---|---|
| `tests/test_models.py` | Domain model creation |
| `tests/test_name_utils.py` | Short name edge cases |
| `tests/test_transform_use_case.py` | Transformation logic (mocked ports) |
| `tests/test_csv_reader.py` | CSV parsing with fixture |
| `tests/test_yaml_writer.py` | YAML format validation |
| `tests/test_json_writer.py` | JSON metadata validation |
| `tests/test_integration.py` | End-to-end pipeline |
