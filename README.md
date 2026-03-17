# ⚡ Apoia-se Exporter

> Ferramenta desktop para análise e exportação de apoiadores do **Apoia-se**, desenvolvida pela **MFW Corp**.

---

## 📋 Sobre o Projeto

O **Apoia-se Exporter** lê o CSV exportado da plataforma Apoia-se e gera um resumo estruturado dos apoiadores por categoria de recompensa, status e período — pronto para uso em vídeos, planilhas e relatórios.

Desenvolvido para uso do canal **@Akitando**.

---

## ✨ Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| 📂 Importar CSV | Seleciona e processa o arquivo exportado do Apoia-se |
| 📊 Dashboard | Cartões de totais + lista de apoiadores por categoria e status |
| 🔍 Buscar | Tabela filtrável por ID, nome ou e-mail |
| 📋 Copiar nomes | Copia a lista de nomes de qualquer grupo com um clique |
| ⚡ Tela de loading | Splash screen durante a inicialização do app |
| 📅 Filtro de dias | Configura a janela de "Apoiadores Ativos Recentes" (10/15/30/45/60 dias) |

---

## 📊 Dados Gerados

### Totais
- **Apoiadores Ativos** — status `Ativo`
- **Pendentes** — status `Aguardando Confirmação`
- **Inadimplentes** — status `Inadimplente`
- **Ativos Recentes (N dias)** — Ativos + outros status com mudança nos últimos N dias
- **Recebido mês atual / mês anterior** — soma dos valores ativos e pendentes

### Por categoria de recompensa
Para cada tier (`5-pesetas`, `18-pesetas`, etc.):
- Lista de apoiadores por status (Ativo, Pendente, Inadimplente, Aguardando, Ativos Recentes)
- Ordenação por **tempo de apoio** (mais antigos primeiro)
- Nomes formatados: `Primeiro Nome` + `Iniciais dos nomes do meio` + `Último Nome`
  - Ex: `Antonio Ismael Rodrigues de Melo` → `Antonio I. R. Melo`
  - Partículas (`de`, `do`, `dos`, `da`, `das`, `di`, `du`) são removidas

---

## 🚀 Como usar

### Executável (recomendado)
1. Baixe o `ApoiaseExporter.exe` na seção [Releases](https://github.com/IsmaelRDeMelo/apoiase-exporter/releases)
2. Execute o arquivo
3. Na aba **Importar CSV**, clique em **Escolher arquivo** e selecione o CSV exportado do Apoia-se
4. Selecione o período para "Apoiadores Ativos Recentes" (padrão: 30 dias)
5. Clique em **⚡ Processar**
6. Acesse o **Dashboard** para ver os resultados

### Desenvolvimento local

```bash
# Clonar o repositório
git clone https://github.com/IsmaelRDeMelo/apoiase-exporter.git
cd apoiase-exporter

# Criar ambiente virtual e instalar dependências
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Rodar o app
python main.py

# Rodar os testes
python -m pytest tests/ -v --cov=src
```

### Gerar o executável

```bash
python build.py
# Resultado em: dist/ApoiaseExporter.exe
```

---

## 🏗️ Arquitetura

O projeto segue **Arquitetura Hexagonal** com os princípios **SOLID** e **DRY**:

```
src/
├── application/
│   └── transform_use_case.py   # Regras de negócio (ETL)
├── domain/
│   ├── models.py               # Entidades de domínio
│   ├── name_utils.py           # Formatação de nomes
│   └── ports.py                # Interfaces (ports)
├── infrastructure/
│   ├── csv_reader.py           # Leitura do CSV (Polars)
│   ├── yaml_writer.py          # Escrita do YAML
│   └── json_writer.py          # Escrita do JSON de metadados
└── gui/
    ├── app.py                   # Janela principal + splash screen
    ├── import_tab.py            # Aba de importação
    ├── dashboard_tab.py         # Aba de dashboard
    └── search_tab.py            # Aba de busca
```

**Tech Stack:**
- `Python 3.11`
- `Polars` — processamento de CSV
- `CustomTkinter` — interface gráfica
- `PyInstaller` — empacotamento do executável
- `pytest` + `pytest-cov` — testes e cobertura

---

## 🧪 Testes

```bash
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

| Módulo | Cobertura |
|---|---|
| `transform_use_case.py` | 99% |
| `models.py` | 100% |
| `name_utils.py` | 100% |
| `csv_reader.py` | 90% |
| `yaml_writer.py` | 100% |
| `json_writer.py` | 100% |

---

## 📁 Artefatos gerados

Após o processamento, os arquivos são salvos em:

```
artifacts/
└── YYYY-MM-DD/
    ├── 001.yaml    # Resumo estruturado
    └── 001.json    # Metadados (ID, nome, e-mail)
```

---

## 🏢 Desenvolvido por

**MFW Corp** · Para o canal [@Akitando](https://www.youtube.com/@akitando)
