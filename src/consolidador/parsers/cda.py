"""
Parser for CDA (Composição e Diversificação das Aplicações) - Portfolio composition data.

CDA files contain detailed asset holdings for each fund, with multiple rows per fund
(one row per asset position).

Supports multiple months for Excel export with one sheet per month.
"""
import pandas as pd
from pathlib import Path
from typing import Optional, Dict

from ..config import (
    CDA_URL_TEMPLATE, CDA_FILES, CDA_MAPPING,
    CSV_ENCODING, CSV_DELIMITER, get_latest_cda_period, get_cda_periods,
    CDA_MONTHS_TO_KEEP
)
from ..downloader import download_zip


def parse_cda(yyyymm: str = None, use_cache: bool = True,
              force: bool = False) -> Optional[pd.DataFrame]:
    """
    Download and parse CDA portfolio composition data.

    Args:
        yyyymm: Period in YYYYMM format (default: previous month)
        use_cache: Use cached file if available
        force: Force re-download

    Returns:
        DataFrame with portfolio composition (multiple rows per fund)
    """
    if yyyymm is None:
        yyyymm = get_latest_cda_period()

    print(f"Processando composição da carteira (CDA {yyyymm})...")

    url = CDA_URL_TEMPLATE.format(yyyymm=yyyymm)
    extract_dir = download_zip(url, use_cache=use_cache, force=force)

    if extract_dir is None:
        print(f"  ✗ Falha ao obter CDA para {yyyymm}")
        return None

    # Parse all BLC files and combine
    all_dfs = []
    total_rows = 0

    for blc_name, file_pattern in CDA_FILES.items():
        filename = file_pattern.format(yyyymm=yyyymm)
        csv_path = extract_dir / filename

        if not csv_path.exists():
            continue

        try:
            df = pd.read_csv(
                csv_path,
                sep=CSV_DELIMITER,
                encoding=CSV_ENCODING,
                low_memory=False,
                dtype=str
            )

            # Apply field mapping
            rename_map = {k: v for k, v in CDA_MAPPING.items() if k in df.columns}
            df = df.rename(columns=rename_map)

            # Keep only mapped columns that exist
            keep_cols = [c for c in CDA_MAPPING.values() if c in df.columns]
            df = df[keep_cols]

            all_dfs.append(df)
            total_rows += len(df)

        except Exception as e:
            print(f"  ⚠ Erro ao processar {filename}: {e}")

    if not all_dfs:
        print("  ✗ Nenhum arquivo CDA processado")
        return None

    # Combine all BLC files
    result = pd.concat(all_dfs, ignore_index=True)

    # Convert numeric fields
    result['valor_mercado'] = _to_float(result.get('valor_mercado'))
    result['valor_custo'] = _to_float(result.get('valor_custo'))
    result['quantidade'] = _to_float(result.get('quantidade'))

    print(f"  ✓ {len(result):,} posições de carteira carregadas")

    # Count unique funds
    if 'cnpj' in result.columns:
        unique_funds = result['cnpj'].nunique()
        print(f"  ✓ {unique_funds:,} fundos com dados de carteira")

    return result


def _to_float(series: Optional[pd.Series]) -> Optional[pd.Series]:
    """Convert series to float, handling Brazilian decimal format."""
    if series is None:
        return None
    return pd.to_numeric(
        series.astype(str).str.replace(',', '.'),
        errors='coerce'
    )


def parse_cda_multiple(use_cache: bool = True, force: bool = False,
                       num_months: int = None) -> Dict[str, pd.DataFrame]:
    """
    Download and parse CDA data for multiple months.

    Args:
        use_cache: Use cached files if available
        force: Force re-download of all months
        num_months: Number of months to fetch (default: CDA_MONTHS_TO_KEEP)

    Returns:
        Dictionary mapping period (YYYY-MM) to DataFrame
    """
    if num_months is None:
        num_months = CDA_MONTHS_TO_KEEP

    periods = get_cda_periods(num_months)
    result = {}

    print(f"\nProcessando {num_months} meses de composição da carteira...")
    print(f"  Períodos: {', '.join(periods)}")

    for yyyymm in periods:
        # Format as YYYY-MM for sheet name
        sheet_name = f"{yyyymm[:4]}-{yyyymm[4:]}"

        df = parse_cda(yyyymm=yyyymm, use_cache=use_cache, force=force)

        if df is not None and not df.empty:
            result[sheet_name] = df
            print(f"  ✓ {sheet_name}: {len(df):,} posições")
        else:
            print(f"  ⚠ {sheet_name}: Sem dados disponíveis")

    print(f"\n✓ {len(result)} meses carregados com sucesso")
    return result
