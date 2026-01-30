# CVM Fundos de Investimento

## Project Overview

Python application for consolidating Brazilian investment fund data from CVM (Comissão de Valores Mobiliários) Open Data Portal using the new CVM Resolution 175 (2023) framework.

## Usage

```bash
python main.py                   # Consolida dados de fundos
python main.py consolidate       # Mesmo que acima
python main.py consolidate --force  # Força re-download
```

## Project Structure

```
fundos-investimento/
├── main.py                  # Entry point
├── src/
│   ├── __init__.py
│   └── consolidador/        # Fund data consolidation package
│       ├── __init__.py
│       ├── config.py        # URLs, field mappings, constants
│       ├── downloader.py    # Download with caching + ZIP extraction
│       ├── consolidator.py  # Main pipeline orchestrator
│       ├── merger.py        # Merge Fund → Class data
│       ├── exporter.py      # CSV export
│       └── parsers/
│           ├── __init__.py
│           └── rcvm175.py   # RCVM175 fund registry parser
└── output/
    ├── fundos_principais.csv  # ~87k funds (one row per fund)
    ├── fundos_classes.csv     # ~35k share classes
    └── cache/                 # Downloaded files cache
```

## Key Technical Details

- **Data Source**: `registro_fundo_classe.zip` (CVM Resolution 175)
- **Output Encoding**: UTF-8-SIG (Excel compatible)

### CSV File Format (CVM Standard)
```python
delimiter = ';'          # NOT comma
encoding = 'latin-1'     # Portuguese characters (ç, ã, etc.)
```

---

## CVM Database Structure (January 2026)

### Critical Finding: Legacy vs New System

| Source | Total Records | Active Funds | Status |
|--------|--------------|--------------|--------|
| `cad_fi.csv` | 46,824 | **32** | ⚠️ Legacy/Deprecated |
| `registro_fundo_classe.zip` | 86,878 | **33,475** | ✅ Current System |

**CVM Resolution 175 (2023)** completely restructured fund registration in Brazil. The old `cad_fi.csv` is essentially frozen - most funds have migrated to the new hierarchical system.

### RCVM175 Data Structure (Three-Table Hierarchy)

```
registro_fundo_classe.zip
├── REGISTRO_FUNDO.CSV      (86,878 funds)
│   ├── ID_Registro_Fundo (PK)
│   ├── CNPJ_Fundo
│   ├── Tipo_Fundo
│   ├── Situacao
│   ├── Patrimonio_Liquido
│   └── Administrator/Manager info
│
├── REGISTRO_CLASSE.CSV     (35,411 share classes)
│   ├── ID_Registro_Classe (PK)
│   ├── ID_Registro_Fundo (FK) ──────┘
│   ├── CNPJ_Classe
│   ├── Classificacao_Anbima (66 categories)
│   ├── Classe_ESG (new!)
│   ├── Publico_Alvo (Geral/Qualificado/Profissional)
│   └── Forma_Condominio (Aberto/Fechado)
│
└── REGISTRO_SUBCLASSE.CSV  (6,615 subclasses)
    ├── ID_Subclasse (PK)
    ├── ID_Registro_Classe (FK) ────┘
    └── Investor segment details
```

### Fund Types in CVM System

| Type | Full Name | RCVM175 Count |
|------|-----------|---------------|
| FI | Fundos de Investimento | 60,444 |
| FIDC | Direitos Creditórios | 7,135 |
| FIF | Fund of Funds | 5,229 |
| FIP | Participações (Private Equity) | 4,203 |
| FII | Imobiliário (Real Estate) | 2,034 |
| FIAGRO | Cadeias Agroindustriais | 272 |
| FITVM | Securities Brokerage | 842 |
| Others | FAPI, FICART, FMIA, FMIEE, FMP-FGTS, FUNCINE | ~2,000 |

### Status Distribution (RCVM175)

| Status | Count | % |
|--------|-------|---|
| Em Funcionamento Normal | 33,475 | 38.6% |
| Cancelado | 50,528 | 58.2% |
| Fase Pré-Operacional | 2,221 | 2.6% |
| Em Liquidação | 638 | 0.7% |

### New Fields in RCVM175

| Field | Description | Business Value |
|-------|-------------|----------------|
| `Classificacao_Anbima` | 66 standardized categories | Better fund comparison |
| `Classe_ESG` | ESG designation (702 funds) | Sustainability tracking |
| `Publico_Alvo` | Investor type | Regulatory compliance |
| `Data_Adaptacao_RCVM175` | Migration date | Track system transition |
| Share Classes | Multiple classes per fund | Investor segmentation |

### Investor Stratification (from REGISTRO_CLASSE)

- **Público Geral** (General Public): 5,616 classes
- **Qualificado** (Qualified Investors): 3,836 classes
- **Profissional** (Professional Investors): 16,744 classes

### Data URLs

```
# Primary source (RCVM175) - USED
https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip

# Legacy source (deprecated) - NOT USED
https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv
```

---

## Output Schema

### fundos_principais.csv

One row per fund (~87k total, ~33k active):

| Column | Source | Description |
|--------|--------|-------------|
| cnpj | REGISTRO_FUNDO | Fund CNPJ (primary key) |
| nome_fundo | REGISTRO_FUNDO | Fund name |
| tipo_fundo | REGISTRO_FUNDO | FI, FII, FIP, FIDC, etc. |
| situacao | REGISTRO_FUNDO | Current status |
| em_funcionamento | Derived | Boolean (active = True) |
| gestor | REGISTRO_FUNDO | Manager name |
| administrador | REGISTRO_FUNDO | Administrator name |
| patrimonio_liquido | REGISTRO_FUNDO | Net assets (R$) |
| classificacao_anbima | REGISTRO_CLASSE | ANBIMA category (aggregated) |
| classe_esg | REGISTRO_CLASSE | ESG designation (S if any class) |
| publico_alvo | REGISTRO_CLASSE | Most restrictive investor type |
| forma_condominio | REGISTRO_CLASSE | Open/Closed |
| taxa_administracao | REGISTRO_CLASSE | Admin fee (%) |
| taxa_performance | REGISTRO_CLASSE | Performance fee (%) |

### fundos_classes.csv

One row per share class (~35k):

| Column | Description |
|--------|-------------|
| cnpj | Fund CNPJ (for linking) |
| cnpj_classe | Class CNPJ |
| nome_classe | Class name |
| classificacao_anbima | ANBIMA classification |
| classe_esg | ESG designation |
| publico_alvo | Investor type |
| taxa_administracao | Admin fee |
| patrimonio_liquido_classe | Class net assets |

---

## Dependencies

```
requests>=2.31.0
pandas>=2.0.0
```
