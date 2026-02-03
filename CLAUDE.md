# CVM Fundos de Investimento

## Project Overview

Python application for consolidating Brazilian investment fund data from CVM (Comissão de Valores Mobiliários) Open Data Portal using the new CVM Resolution 175 (2023) framework.

Automated daily updates via GitHub Actions with Google Drive integration.

## Usage

```bash
python main.py                      # Consolida dados de fundos
python main.py consolidate          # Mesmo que acima
python main.py consolidate --force  # Força re-download
python main.py auth                 # Autenticar com Google (uma vez)
python main.py upload               # Upload para Google Drive
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
│       ├── exporter.py      # CSV/Excel export
│       ├── uploader.py      # Google Drive upload (OAuth2)
│       └── parsers/
│           ├── __init__.py
│           ├── rcvm175.py   # RCVM175 fund registry parser
│           └── cda.py       # CDA portfolio composition parser
├── .github/
│   └── workflows/
│       └── consolidar-fundos.yml  # Daily automation (08:30 BRT)
└── output/
    ├── fundos.csv                 # ~33k active funds
    ├── composicao_carteira.xlsx   # ~3M positions (5 months, 1 sheet/month)
    └── cache/                     # Downloaded files cache
```

## Key Technical Details

- **Data Source**: `registro_fundo_classe.zip` (CVM Resolution 175)
- **Portfolio Data**: `cda_fi_YYYYMM.zip` (Composição e Diversificação) - 5 months
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

### composicao_carteira.xlsx

Excel file with **one sheet per month** (last 5 months). Each sheet contains:

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

## Automation

### GitHub Actions

Daily workflow at 08:30 BRT (11:30 UTC):
1. Downloads fresh data from CVM
2. Consolidates fund registry + portfolio composition
3. Uploads to Google Drive
4. Saves artifacts as backup

### Google Drive Integration

Uses OAuth2 for authentication. Setup:
1. Create OAuth2 Web App credentials in Google Cloud Console
2. Run `python main.py auth` locally to generate token
3. Add secrets to GitHub: `GOOGLE_TOKEN_JSON`, `GOOGLE_DRIVE_FOLDER_ID`

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
openpyxl>=3.1.0
google-api-python-client>=2.100.0
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
```
