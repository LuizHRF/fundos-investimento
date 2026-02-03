"""
Export module - Writes consolidated data to files.

Output files:
- fundos.csv: Fund data + class essentials (one row per fund, active only)
- composicao_carteira.xlsx: Portfolio composition with one sheet per month
"""
import re
import pandas as pd
from pathlib import Path
from typing import Optional, Dict

from .config import OUTPUT_DIR, OUTPUT_ENCODING, OUTPUT_COLUMNS_CARTEIRA


# Regex to match illegal Excel characters (control chars except tab, newline, carriage return)
ILLEGAL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')


def clean_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Remove illegal characters from string columns for Excel compatibility."""
    df = df.copy()
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(
            lambda x: ILLEGAL_CHARS_RE.sub('', str(x)) if pd.notna(x) else x
        )
    return df


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


def export_carteira_excel(data: Dict[str, pd.DataFrame],
                          filename: str = "composicao_carteira.xlsx") -> Optional[Path]:
    """
    Export composicao_carteira.xlsx with one sheet per month.

    Args:
        data: Dictionary mapping sheet name (YYYY-MM) to DataFrame
        filename: Output filename

    Returns:
        Path to the exported file
    """
    if not data:
        print("\n⚠ Nenhum dado de carteira para exportar")
        return None

    ensure_output_dir()
    output_path = OUTPUT_DIR / filename

    print(f"\nExportando composição da carteira para Excel...")

    # Sort sheets by date (most recent first)
    sorted_sheets = sorted(data.keys(), reverse=True)

    total_positions = 0
    total_funds = set()

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name in sorted_sheets:
            df = data[sheet_name]

            # Select and order columns
            available_cols = [c for c in OUTPUT_COLUMNS_CARTEIRA if c in df.columns]
            output_df = df[available_cols].copy()

            # Clean illegal characters for Excel
            output_df = clean_for_excel(output_df)

            # Write to sheet
            output_df.to_excel(writer, sheet_name=sheet_name, index=False)

            total_positions += len(output_df)
            if 'cnpj' in output_df.columns:
                total_funds.update(output_df['cnpj'].unique())

            print(f"  ✓ {sheet_name}: {len(output_df):,} posições")

    print(f"\n✓ {total_positions:,} posições exportadas para {output_path}")
    print(f"  ({len(total_funds):,} fundos únicos em {len(sorted_sheets)} meses)")

    return output_path


def print_summary(fundos_df: pd.DataFrame, carteira_data: Optional[Dict[str, pd.DataFrame]] = None):
    """Print summary statistics."""
    print("\n" + "=" * 50)
    print("RESUMO")
    print("=" * 50)

    print(f"\nFundos ativos: {len(fundos_df):,}")

    if 'tipo_fundo' in fundos_df.columns:
        print("\nPor tipo:")
        for tipo, count in fundos_df['tipo_fundo'].value_counts().head(8).items():
            print(f"  {tipo}: {count:,}")

    if carteira_data:
        total_positions = sum(len(df) for df in carteira_data.values())
        print(f"\nComposição da carteira:")
        print(f"  Meses disponíveis: {len(carteira_data)}")
        print(f"  Total de posições: {total_positions:,}")

        # Show most recent month's breakdown
        most_recent = sorted(carteira_data.keys(), reverse=True)[0]
        df = carteira_data[most_recent]
        if 'tipo_aplicacao' in df.columns:
            print(f"\nPor tipo de aplicação ({most_recent}):")
            for tipo, count in df['tipo_aplicacao'].value_counts().head(5).items():
                print(f"  {tipo}: {count:,}")

    print("\n" + "=" * 50)
