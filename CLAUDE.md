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
│           ├── rcvm175.py   # RCVM175 fund registry parser
│           └── cda.py       # CDA portfolio composition parser
└── output/
    ├── fundos.csv              # ~33k active funds
    ├── composicao_carteira.csv # ~350k portfolio positions
    └── cache/                  # Downloaded files cache
```

## Key Technical Details

- **Data Source**: `registro_fundo_classe.zip` (CVM Resolution 175)
- **Portfolio Data**: `cda_fi_YYYYMM.zip` (Composição e Diversificação)
- **Output Encoding**: UTF-8-SIG (Excel compatible)
- **CNPJ Format**: Prefixed with `'` for Excel text handling

### CSV File Format (CVM Standard)
```python
delimiter = ';'          # NOT comma
encoding = 'latin-1'     # Portuguese characters (ç, ã, etc.)
```

---

## Output Schema

### fundos.csv

One row per active fund (~33k):

| Column | Description |
|--------|-------------|
| cnpj | Fund CNPJ (primary key, text format) |
| nome_fundo | Fund name |
| tipo_fundo | FI, FII, FIP, FIDC, FIAGRO, etc. |
| gestor | Manager name |
| administrador | Administrator name |
| custodiante | Custodian name |
| patrimonio_liquido | Net assets (R$) |
| classificacao_anbima | ANBIMA category |
| publico_alvo | Investor type |

### composicao_carteira.csv

Multiple rows per fund (~350k positions):

| Column | Description |
|--------|-------------|
| cnpj | Fund CNPJ (foreign key to fundos.csv) |
| tipo_aplicacao | Application type (Títulos Públicos, Ações, etc.) |
| tipo_ativo | Asset type |
| descricao_ativo | Asset description |
| emissor | Issuer name |
| valor_mercado | Market value (R$) |
| quantidade | Quantity |
| data_competencia | Reference date |

---

## Data URLs

```
# Fund registry (RCVM175)
https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip

# Portfolio composition (CDA)
https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS/cda_fi_YYYYMM.zip
```

---

## Dependencies

```
requests>=2.31.0
pandas>=2.0.0
```
