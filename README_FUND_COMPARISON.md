# Fund Comparison System

Comprehensive system for comparing Brazilian investment funds using CVM Open Data.

## Features

✅ **Data Acquisition**
- Downloads and parses CVM CSV files (cad_fi.csv, extrato_fi.csv)
- Handles Brazilian CSV format (`;` delimiter, `latin-1` encoding)
- Intelligent caching to avoid repeated downloads
- Automatic data merging using CNPJ as primary key

✅ **Unified Data Model**
- Single `Fund` dataclass combining registration, fees, and policies
- Supports all fund types: FI, FII, FIP, FIDC, FIAGRO, FIE
- Flexible metadata storage for fund-specific attributes

✅ **SQLite Database**
- Local persistence for fast queries
- Automatic change tracking (fees, managers, status)
- Indexed searches by multiple criteria

✅ **Fund Search & Filtering**
- Filter by status, type, manager, ANBIMA class
- Minimum net worth filtering
- Target audience filtering (public, qualified, professional)

✅ **Fund Comparison**
- Side-by-side comparison of multiple funds
- Comparison across: fees, management, financial metrics
- CSV export for further analysis

✅ **Change Tracking**
- Automatic detection of:
  - Fee changes (admin fee, performance fee)
  - Manager/administrator changes
  - Status changes (active → canceled)
  - Historical audit trail

## Quick Start

### 1. Install Dependencies

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Load Fund Data

```bash
python3 fund_analyzer.py
```

This will:
- Download fund registration data (~46K funds)
- Download fund policies/fees data
- Merge data using CNPJ
- Store in SQLite database (`funds.db`)

**Note**: First run takes ~2-3 minutes to download and process data.

### 3. Run Comparison Demo

```bash
python3 compare_funds.py
```

This demonstrates:
- Fund statistics
- Searching by criteria
- Side-by-side comparison
- Change tracking
- CSV export

## Usage Examples

### Basic Search

```python
from fund_analyzer import FundAnalyzer

analyzer = FundAnalyzer()

# Search for active funds
results = analyzer.database.search_funds({
    'status': 'EM FUNCIONAMENTO NORMAL',
    'fund_type': 'FI'
})

for fund in results:
    print(f"{fund['name']} - Admin Fee: {fund['admin_fee']}%")
```

### Fund Comparison

```python
# Compare 3 specific funds by CNPJ
cnpj_list = [
    '00.017.024/0001-53',
    '00.068.305/0001-35',
    '00.071.477/0001-68'
]

comparison = analyzer.compare_funds(cnpj_list)

# Export to CSV
analyzer.export_comparison_csv(cnpj_list, 'my_comparison.csv')
```

### Advanced Filtering

```python
# Find large Renda Fixa funds
results = analyzer.database.search_funds({
    'status': 'EM FUNCIONAMENTO NORMAL',
    'anbima_class': 'Renda Fixa',
    'min_net_worth': 1000000  # R$ 1M minimum
})
```

### Track Changes

```python
# Get recent changes across all funds
changes = analyzer.database.get_fund_changes(limit=50)

for change in changes:
    print(f"{change['cnpj']}: {change['field_name']}")
    print(f"  {change['old_value']} → {change['new_value']}")

# Get changes for specific fund
fund_changes = analyzer.database.get_fund_changes(
    cnpj='00.017.024/0001-53',
    limit=10
)
```

### Get Statistics

```python
stats = analyzer.get_statistics()

print(f"Total funds: {stats['total_funds']}")
print(f"Active funds: {stats['active_funds']}")

# Top managers
for manager in stats['top_managers']:
    print(f"{manager['manager']}: {manager['fund_count']} funds")

# By ANBIMA class
for anbima_class, count in stats['top_anbima_classes'].items():
    print(f"{anbima_class}: {count} funds")
```

## Database Schema

### `funds` table
Main fund information:
- `cnpj` (PRIMARY KEY)
- `name`, `fund_type`, `status`
- `manager`, `manager_cnpj`
- `administrator`, `admin_cnpj`
- `custodian`, `auditor`
- `anbima_class`, `classe`
- `target_audience`, `exclusive`
- `admin_fee`, `performance_fee`
- `net_worth`, `net_worth_date`

### `fund_metadata` table
Flexible additional attributes:
- `cnpj` (FOREIGN KEY)
- `key`, `value`

Examples:
- `condom`: Condominium type (ABERTO/FECHADO)
- `minimum_investment`: Minimum application value
- `redemption_days`: Days until redemption
- `payment_days`: Days until payment

### `fund_history` table
Change tracking:
- `cnpj` (FOREIGN KEY)
- `change_type`: Type of change (UPDATE, INSERT, DELETE)
- `field_name`: Which field changed
- `old_value`, `new_value`: Before/after values
- `changed_at`: Timestamp

## Data Sources

### cad_fi.csv (Fund Registration)
- `CNPJ_FUNDO`: Tax ID (primary key)
- `DENOM_SOCIAL`: Fund name
- `GESTOR`, `ADMIN`: Manager and administrator
- `TAXA_ADM`, `TAXA_PERFM`: Fees
- `SIT`: Status (EM FUNCIONAMENTO NORMAL, CANCELADA, etc.)
- `CLASSE_ANBIMA`: ANBIMA classification
- `VL_PATRIM_LIQ`: Net worth

### extrato_fi.csv (Fund Policies)
- `CNPJ_FUNDO_CLASSE`: Fund CNPJ
- `APLIC_MIN`: Minimum investment
- `QT_DIA_RESGATE_COTAS`: Redemption days
- `QT_DIA_PAGTO_RESGATE`: Payment days
- Investment policy limits

## Fund Status Values

The CVM data uses these status values:

| Status | Count | Meaning |
|--------|-------|---------|
| `CANCELADA` | ~40,844 | Canceled/Closed |
| `LIQUIDAÇÃO` | ~123 | In liquidation |
| `FASE PRÉ-OPERACIONAL` | ~105 | Pre-operational |
| `EM FUNCIONAMENTO NORMAL` | ~30 | **Active** (use this for filtering) |
| `INCORPORAÇÃO` | ~10 | Being incorporated |
| `EM ANÁLISE` | ~5 | Under analysis |
| `EM SITUAÇÃO ESPECIAL` | ~4 | Special situation |

**Important**: Use `status = 'EM FUNCIONAMENTO NORMAL'` to find active funds.

## Cache Behavior

- **Data cache**: Downloaded CSVs are cached in `./data_cache/` for 1 hour
- **Database**: SQLite database in `./funds.db` persists across runs
- **Incremental updates**: Re-running the load will update existing records and track changes

## Output Files

- `funds.db`: SQLite database with all fund data
- `fund_comparison.csv`: Example comparison export
- `data_cache/`: Downloaded CSV files (for performance)

## Performance

- **Initial load**: ~2-3 minutes (downloads ~50MB of data)
- **Subsequent loads**: ~30 seconds (uses cache)
- **Search queries**: < 100ms (SQLite indexed)
- **Database size**: ~25MB (41K+ funds)

## Extending the System

### Add New Data Sources

```python
class CVMDataDownloader:
    def get_monthly_profile(self, year_month: str):
        """Download perfil_mensal_fi_YYYYMM.csv"""
        url = f"{self.BASE_URL}/FI/DOC/PERFIL_MENSAL/DADOS/perfil_mensal_fi_{year_month}.csv"
        return self.download_csv(url)
```

### Add New Search Filters

```python
# In FundDatabase.search_funds()
if 'administrator' in filters:
    query += " AND administrator LIKE ?"
    params.append(f"%{filters['administrator']}%")
```

### Add New Statistics

```python
# In FundAnalyzer.get_statistics()
cursor.execute("""
    SELECT custodian, COUNT(*) as count
    FROM funds
    WHERE status = 'EM FUNCIONAMENTO NORMAL' AND custodian IS NOT NULL
    GROUP BY custodian
    ORDER BY count DESC
    LIMIT 10
""")
stats['top_custodians'] = {row[0]: row[1] for row in cursor.fetchall()}
```

## Next Steps

Potential enhancements:

1. **ZIP file support**: Extract compressed datasets (perfil_mensal, inf_diario)
2. **Time series analysis**: Track fund performance over time using monthly profiles
3. **Portfolio composition**: Analyze fund holdings from CDA files
4. **Risk metrics**: Calculate Sharpe ratio, volatility from historical data
5. **Excel export**: Enhanced export with formatting using openpyxl
6. **Web API**: Flask/FastAPI wrapper for REST access
7. **Scheduled updates**: Cron job to automatically refresh data daily

## Troubleshooting

### "No active funds found"
- Make sure you're using `status = 'EM FUNCIONAMENTO NORMAL'` not `'ATIVA'`
- CVM uses Portuguese status values

### "Database locked"
- Only one process can write to SQLite at a time
- Close other connections before loading data

### "latin-1 codec can't decode"
- Ensure you're using `encoding='latin-1'` for CVM CSV files
- Default UTF-8 won't work with Portuguese characters

## API Reference

See docstrings in `fund_analyzer.py` for complete API documentation.

### Key Classes

- `Fund`: Dataclass representing a unified fund
- `CVMDataDownloader`: Downloads and caches CVM CSV files
- `FundDatabase`: SQLite persistence and querying
- `FundAnalyzer`: High-level analysis and comparison

### Key Methods

- `FundAnalyzer.load_fund_data()`: Load data from CVM
- `FundAnalyzer.compare_funds(cnpj_list)`: Compare multiple funds
- `FundAnalyzer.get_statistics()`: Get overall statistics
- `FundDatabase.search_funds(filters)`: Search with criteria
- `FundDatabase.get_fund_changes()`: Get change history
- `FundAnalyzer.export_comparison_csv()`: Export comparison

## License

This project uses public data from CVM (Comissão de Valores Mobiliários) Open Data Portal.
Data usage subject to CVM terms and conditions.
