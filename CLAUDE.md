# CVM Investment Funds Dashboard

## Project Overview

Python application that monitors Brazilian investment fund data from CVM (Comissão de Valores Mobiliários) Open Data Portal. Tracks 22 datasets across 7 fund types (FI, FII, FIP, FIDC, FIAGRO, FIE).

## Key Technical Details

- **API**: CKAN API via `ckanapi` library (https://dados.cvm.gov.br)
- **Main class**: `CVMDataExtractor` in `script.py`
- **State persistence**: `cvm_state.json` for change tracking between runs

### CSV File Format (Important)
```python
# All CVM CSVs use:
delimiter = ';'          # NOT comma
encoding = 'latin-1'     # Portuguese characters (ç, ã, etc.)
```

## Change Detection Mechanism

The script detects modifications by comparing **metadata timestamps** from the CKAN API:

- **Datasets**: `metadata_modified` field
- **Resources**: `last_modified` field

**Limitation**: Does not download files or compute hashes. If CVM silently replaces a file without updating timestamps, the change won't be detected.

## Dataset Structure & Common Keys

| Dataset | Key Fields | Content |
|---------|------------|---------|
| `cad_fi.csv` | `CNPJ_FUNDO`, `CD_CVM` | Fund registration, admin, manager |
| `extrato_fi.csv` | `CNPJ_FUNDO_CLASSE` | Fund policies, fees, investment rules |
| `perfil_mensal_fi_*.csv` | `CNPJ_FUNDO` | Monthly profiles |
| `dfin_fii_*.csv` | CNPJ | Financial statements |

**Primary join key**: `CNPJ_FUNDO` (Brazilian tax ID) - present across most datasets.

### Data Dictionaries (Dicionário de Dados)

Each of the 22 datasets includes a **"Dicionário de dados"** resource that documents:
- Field names and descriptions
- Data types and formats
- Relationships between fields

These dictionaries are essential for:
- Understanding field semantics across different CSVs within a dataset
- Correctly joining documents within the same dataset
- Mapping equivalent fields across different fund types

## Example CSV URLs

```
https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv
https://dados.cvm.gov.br/dados/FI/DOC/EXTRATO/DADOS/extrato_fi.csv
https://dados.cvm.gov.br/dados/FI/DOC/PERFIL_MENSAL/DADOS/perfil_mensal_fi_YYYYMM.csv
https://dados.cvm.gov.br/dados/FII/DOC/DFIN/DADOS/dfin_fii_YYYY.csv
```

## Expansion Possibility: Holistic Data Analysis

Currently the script only monitors metadata changes. It could be extended to download and analyze the actual fund data by joining datasets on CNPJ.

### Potential Analysis Capabilities

- Join registration data with financial data
- Track fund performance over time series
- Analyze fund characteristics vs. fees/returns
- Compare across fund types (FI vs FII vs FIP)
- Aggregate by manager, administrator, or asset class

### Implementation Approach

```python
import pandas as pd

# Download and parse (note: semicolon delimiter, latin-1 encoding)
df_cad = pd.read_csv(url_cad, sep=';', encoding='latin-1')
df_extrato = pd.read_csv(url_extrato, sep=';', encoding='latin-1')

# Join on CNPJ
df_merged = df_cad.merge(
    df_extrato,
    left_on='CNPJ_FUNDO',
    right_on='CNPJ_FUNDO_CLASSE'
)
```

### Dependencies to Add

```
pandas>=2.0
```

## Running the Project

```bash
source .venv/bin/activate
python3 script.py
```

Outputs generated:
- `cvm_dashboard.txt` - Text dashboard
- `cvm_state.json` - Cached state for change tracking
- `cvm_fundos_completo.json` - Complete catalog
- `cvm_fundos_recursos.csv` - Resources list
- `cvm_metadata_summary.json` - Statistical summary

---

## NEXT STEPS: Fund Comparison System

### Goal
Build a comprehensive fund comparison system to track all available investment funds and their features for corporate investment decision-making.

### Implementation Todo List

#### Phase 1: Data Understanding
- [ ] Analyze Dicionário de Dados for each dataset type to map field semantics

#### Phase 2: Data Acquisition
- [ ] Implement ZIP file download and extraction for compressed datasets
- [ ] Implement CSV download and parsing (delimiter=';', encoding='latin-1')
- [ ] Implement incremental updates (only download changed files based on last_modified)

#### Phase 3: Data Model & Integration
- [ ] Design unified fund data model with common attributes across fund types
- [ ] Create fund catalog from cad_fi.csv (registration data: CNPJ, name, manager, admin, status)
- [ ] Integrate fee data from extrato_fi.csv (TAXA_ADM, TAXA_PERFM, policies)
- [ ] Integrate financial metrics from perfil_mensal/inf_diario (PL, returns, quotas)
- [ ] Handle different fund types: FI, FII, FIP, FIDC, FIAGRO, FIE with their specific datasets
- [ ] Implement data joining using CNPJ_FUNDO as primary key across datasets

#### Phase 4: Storage & Persistence
- [ ] Create local SQLite database to store processed fund data

#### Phase 5: Analysis & Comparison
- [ ] Build fund search and filtering (by type, manager, fees, status, asset class)
- [ ] Build fund comparison report generator (side-by-side feature comparison)
- [ ] Add fund change tracking (detect new funds, closed funds, fee changes)
- [ ] Create export functionality (CSV/Excel comparison reports)
- [ ] Create a compreensive fund comparison (csv table that encompasses all funds and their stats)
---

## Available Data Fields by Dataset

### cad_fi.csv (Fund Registration)
```
TP_FUNDO, CNPJ_FUNDO, DENOM_SOCIAL, DT_REG, DT_CONST, CD_CVM, DT_CANCEL,
SIT, DT_INI_SIT, DT_INI_ATIV, DT_INI_EXERC, DT_FIM_EXERC, CLASSE,
DT_INI_CLASSE, RENTAB_FUNDO, CONDOM, FUNDO_COTAS, FUNDO_EXCLUSIVO,
TRIB_LPRAZO, PUBLICO_ALVO, ENTID_INVEST, TAXA_PERFM, INF_TAXA_PERFM,
TAXA_ADM, INF_TAXA_ADM, VL_PATRIM_LIQ, DT_PATRIM_LIQ, DIRETOR,
CNPJ_ADMIN, ADMIN, PF_PJ_GESTOR, CPF_CNPJ_GESTOR, GESTOR,
CNPJ_AUDITOR, AUDITOR, CNPJ_CUSTODIANTE, CUSTODIANTE,
CNPJ_CONTROLADOR, CONTROLADOR, INVEST_CEMPR_EXTER, CLASSE_ANBIMA
```

### perfil_mensal (Monthly Profile)
```
TP_FUNDO_CLASSE, CNPJ_FUNDO_CLASSE, DENOM_SOCIAL, DT_COMPTC, VERSAO,
NR_COTST_PF_*, NR_COTST_PJ_*, NR_COTST_BANCO, NR_COTST_CORRETORA_DISTRIB,
PR_PL_COTST_* (% of AUM by investor type),
PR_VARIACAO_DIARIA_COTA, PR_VARIACAO_DIARIA_COTA_ESTRESSE,
CENARIO_FPR_IBOVESPA, CENARIO_FPR_JUROS, CENARIO_FPR_CUPOM, CENARIO_FPR_DOLAR,
VL_FATOR_RISCO_NOCIONAL_LONG_*, VL_FATOR_RISCO_NOCIONAL_SHORT_*,
PR_PATRIM_LIQ_MAIOR_COTST, NR_DIA_CINQU_PERC, NR_DIA_CEM_PERC,
ST_LIQDEZ, PR_PATRIM_LIQ_CONVTD_CAIXA
```

### fip-inf_quadrimestral (Private Equity Reports)
```
TP_FUNDO_CLASSE, CNPJ_FUNDO_CLASSE, DENOM_SOCIAL, DT_COMPTC,
VL_PATRIM_LIQ, QT_COTA, VL_PATRIM_COTA, NR_COTST,
VL_CAP_COMPROM, VL_CAP_SUBSCR, VL_CAP_INTEGR,
NR_COTST_SUBSCR_*, PR_COTA_SUBSCR_*
```

---

## Suggested Analyses

### 1. Fund Selection & Screening
| Analysis | Data Source | Fields |
|----------|-------------|--------|
| Active funds by type (FI, FII, FIP, FIDC, FIAGRO) | `cad_fi.csv` | `SIT`, `TP_FUNDO`, `CLASSE` |
| Funds by target audience | `cad_fi.csv` | `PUBLICO_ALVO` (general, qualified, professional) |
| Funds by ANBIMA classification | `cad_fi.csv` | `CLASSE_ANBIMA` (Renda Fixa, Multimercado, Ações, etc.) |
| Minimum investment requirements | `extrato_fi.csv` | `APLIC_MIN` |
| Exclusive vs. open funds | `cad_fi.csv` | `FUNDO_EXCLUSIVO`, `CONDOM` |

### 2. Fee Analysis & Comparison
| Analysis | Data Source | Fields |
|----------|-------------|--------|
| Administration fee comparison | `cad_fi.csv`, `extrato_fi.csv` | `TAXA_ADM` |
| Performance fee analysis | `cad_fi.csv`, `extrato_fi.csv` | `TAXA_PERFM`, `PARAM_TAXA_PERFM` |
| Entry/exit fees | `extrato_fi.csv` | `TAXA_INGRESSO_*`, `TAXA_SAIDA_*` |
| Fee vs. returns correlation | Combined | Fees + `perfil_mensal` returns |

### 3. Manager & Administrator Analysis
| Analysis | Data Source | Fields |
|----------|-------------|--------|
| Top managers by AUM | `cad_fi.csv` | `GESTOR`, `VL_PATRIM_LIQ` |
| Top administrators by fund count | `cad_fi.csv` | `ADMIN`, `CNPJ_ADMIN` |
| Manager concentration risk | `cad_fi.csv` | Aggregate by `CPF_CNPJ_GESTOR` |
| Custodian market share | `cad_fi.csv` | `CUSTODIANTE` |

### 4. Risk & Portfolio Analysis
| Analysis | Data Source | Fields |
|----------|-------------|--------|
| Daily volatility (VaR proxy) | `perfil_mensal` | `PR_VARIACAO_DIARIA_COTA`, `PR_VARIACAO_DIARIA_COTA_ESTRESSE` |
| Exposure to risk factors | `perfil_mensal` | `CENARIO_FPR_IBOVESPA`, `CENARIO_FPR_JUROS`, `CENARIO_FPR_DOLAR` |
| Derivatives exposure | `perfil_mensal` | `VL_FATOR_RISCO_NOCIONAL_*` |
| Credit risk (private credit %) | `extrato_fi.csv` | `ATIVO_CRED_PRIV`, `APLIC_MAX_ATIVO_CRED_PRIV` |
| Foreign investment exposure | `extrato_fi.csv` | `INVEST_EXTERIOR`, `APLIC_MAX_ATIVO_EXTERIOR` |

### 5. Liquidity Analysis
| Analysis | Data Source | Fields |
|----------|-------------|--------|
| Redemption terms | `extrato_fi.csv` | `QT_DIA_RESGATE_COTAS`, `QT_DIA_PAGTO_RESGATE` |
| Conversion period | `extrato_fi.csv` | `QT_DIA_CONVERSAO_COTA` |
| Portfolio liquidity | `perfil_mensal` | `NR_DIA_CINQU_PERC`, `NR_DIA_CEM_PERC`, `ST_LIQDEZ` |
| Cash position | `perfil_mensal` | `PR_PATRIM_LIQ_CONVTD_CAIXA` |

### 6. Investor Base Analysis
| Analysis | Data Source | Fields |
|----------|-------------|--------|
| Investor type distribution | `perfil_mensal` | `NR_COTST_PF_*`, `NR_COTST_PJ_*`, `NR_COTST_BANCO`, etc. |
| Institutional vs. retail | `perfil_mensal` | `PR_PL_COTST_*` (% of AUM by type) |
| Concentration risk (top investor) | `perfil_mensal` | `PR_PATRIM_LIQ_MAIOR_COTST` |
| Pension fund participation | `perfil_mensal` | `NR_COTST_EFPC`, `NR_COTST_RPPS`, `NR_COTST_EAPC` |

### 7. FII-Specific (Real Estate Funds)
| Analysis | Data Source | Fields |
|----------|-------------|--------|
| Financial statements analysis | `fii-doc-dfin` | Balance sheet, income statement |
| Monthly/quarterly performance | `fii-doc-inf_mensal/trimestral` | Detailed FII metrics |
| Dividend distribution | `fii-doc-inf_*` | Distribution data |

### 8. FIP-Specific (Private Equity)
| Analysis | Data Source | Fields |
|----------|-------------|--------|
| Committed vs. called capital | `fip-inf_quadrimestral` | `VL_CAP_COMPROM`, `VL_CAP_SUBSCR`, `VL_CAP_INTEGR` |
| Investor composition | `fip-inf_quadrimestral` | `NR_COTST_SUBSCR_*`, `PR_COTA_SUBSCR_*` |
| NAV per share evolution | `fip-inf_quadrimestral` | `VL_PATRIM_COTA` |

### 9. Time Series & Trends
| Analysis | Data Source | Fields |
|----------|-------------|--------|
| AUM evolution over time | `perfil_mensal` (monthly) | `VL_PATRIM_LIQ` |
| New fund launches | `cad_fi.csv` | `DT_REG`, `DT_CONST` |
| Fund closures/cancellations | `cad_fi.csv` | `DT_CANCEL`, `SIT` |
| Industry growth by segment | Combined | Aggregate by `CLASSE_ANBIMA` |

### 10. Compliance & Regulatory
| Analysis | Data Source | Fields |
|----------|-------------|--------|
| Document delivery status | `fi-doc-entrega` | Delivery tracking |
| Regulatory events | `fi-doc-eventual` | Special events/disclosures |
| Assembly voting patterns | `perfil_mensal` | `VOTO_ADMIN_ASSEMB` |

---

## Priority Analyses for Corporate Investment

1. **Fund Screening Dashboard**: Filter by `PUBLICO_ALVO`, `CLASSE_ANBIMA`, `SIT=ATIVO`
2. **Fee Comparison Matrix**: Compare `TAXA_ADM` and `TAXA_PERFM` across similar funds
3. **Risk Profile Assessment**: Use `PR_VARIACAO_DIARIA_COTA` and stress scenarios
4. **Liquidity Requirements Match**: Check `QT_DIA_RESGATE_COTAS` meets corporate needs
5. **Manager Due Diligence**: Track record by `GESTOR` across multiple funds

---

## Dependencies to Add for Full Implementation

```
pandas>=2.0
sqlalchemy>=2.0
openpyxl>=3.0      # Excel export
```
