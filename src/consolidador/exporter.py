"""
Export module - Writes consolidated data to CSV files.

Output files:
- fundos.csv: Fund data + class essentials (one row per fund, active only)
- composicao_carteira.csv: Portfolio composition (multiple rows per fund)
"""
import pandas as pd
from pathlib import Path
from typing import Optional

from .config import OUTPUT_DIR, OUTPUT_ENCODING, OUTPUT_COLUMNS_CARTEIRA


def ensure_output_dir() -> Path:
    """Ensure output directory exists."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def export_fundos(df: pd.DataFrame, filename: str = "fundos.csv") -> Path:
    """Export fundos.csv."""
    ensure_output_dir()
    output_path = OUTPUT_DIR / filename

    df.to_csv(output_path, index=False, encoding=OUTPUT_ENCODING)

    print(f"\n✓ {len(df):,} fundos exportados para {output_path}")
    return output_path


def export_carteira(df: Optional[pd.DataFrame], filename: str = "composicao_carteira.csv") -> Optional[Path]:
    """Export composicao_carteira.csv."""
    if df is None or df.empty:
        print("\n⚠ Nenhum dado de carteira para exportar")
        return None

    ensure_output_dir()
    output_path = OUTPUT_DIR / filename

    # Select and order columns
    available_cols = [c for c in OUTPUT_COLUMNS_CARTEIRA if c in df.columns]
    output_df = df[available_cols].copy()

    # Format CNPJ as text for Excel
    if 'cnpj' in output_df.columns:
        output_df['cnpj'] = "'" + output_df['cnpj'].astype(str)

    output_df.to_csv(output_path, index=False, encoding=OUTPUT_ENCODING)

    unique_funds = output_df['cnpj'].nunique() if 'cnpj' in output_df.columns else 0
    print(f"✓ {len(output_df):,} posições exportadas para {output_path}")
    print(f"  ({unique_funds:,} fundos com dados de carteira)")

    return output_path


def print_summary(fundos_df: pd.DataFrame, carteira_df: Optional[pd.DataFrame] = None):
    """Print summary statistics."""
    print("\n" + "=" * 50)
    print("RESUMO")
    print("=" * 50)

    print(f"\nFundos ativos: {len(fundos_df):,}")

    if 'tipo_fundo' in fundos_df.columns:
        print("\nPor tipo:")
        for tipo, count in fundos_df['tipo_fundo'].value_counts().head(8).items():
            print(f"  {tipo}: {count:,}")

    if carteira_df is not None and not carteira_df.empty:
        print(f"\nComposição da carteira: {len(carteira_df):,} posições")
        if 'tipo_aplicacao' in carteira_df.columns:
            print("\nPor tipo de aplicação:")
            for tipo, count in carteira_df['tipo_aplicacao'].value_counts().head(5).items():
                print(f"  {tipo}: {count:,}")

    print("\n" + "=" * 50)
