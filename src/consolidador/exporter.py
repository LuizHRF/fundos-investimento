"""
Export module - Writes consolidated data to CSV files.

Output files:
- fundos_principais.csv: One row per fund (~87k funds, ~33k active)
- fundos_classes.csv: One row per share class (~35k classes)
"""
import pandas as pd
from pathlib import Path
from typing import Optional

from .config import OUTPUT_DIR, OUTPUT_ENCODING


def ensure_output_dir() -> Path:
    """Ensure output directory exists and return its path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def export_principais(df: pd.DataFrame, filename: str = "fundos_principais.csv") -> Path:
    """
    Export fundos_principais.csv with UTF-8-SIG encoding.

    Args:
        df: DataFrame to export
        filename: Output filename

    Returns:
        Path to exported file
    """
    ensure_output_dir()
    output_path = OUTPUT_DIR / filename

    df.to_csv(
        output_path,
        index=False,
        encoding=OUTPUT_ENCODING
    )

    active_count = df['em_funcionamento'].sum() if 'em_funcionamento' in df.columns else 'N/A'
    print(f"\n✓ {len(df)} fundos exportados para {output_path}")
    print(f"  ({active_count} em funcionamento normal)")
    return output_path


def export_classes(df: Optional[pd.DataFrame], filename: str = "fundos_classes.csv") -> Optional[Path]:
    """
    Export fundos_classes.csv with UTF-8-SIG encoding.

    Args:
        df: DataFrame to export (may be None or empty)
        filename: Output filename

    Returns:
        Path to exported file, or None if no data
    """
    if df is None or df.empty:
        print("\n⚠ Nenhum dado de classes para exportar")
        return None

    ensure_output_dir()
    output_path = OUTPUT_DIR / filename

    df.to_csv(
        output_path,
        index=False,
        encoding=OUTPUT_ENCODING
    )

    print(f"✓ {len(df)} classes exportadas para {output_path}")
    return output_path


def print_summary(principais_df: pd.DataFrame, classes_df: Optional[pd.DataFrame] = None):
    """Print summary statistics of the consolidation."""
    print("\n" + "=" * 60)
    print("RESUMO DA CONSOLIDAÇÃO RCVM175")
    print("=" * 60)

    print(f"\nFundos Totais: {len(principais_df)}")

    if 'em_funcionamento' in principais_df.columns:
        active = principais_df['em_funcionamento'].sum()
        print(f"  - Em funcionamento: {active}")
        print(f"  - Outros status: {len(principais_df) - active}")

    if 'tipo_fundo' in principais_df.columns:
        print("\nPor tipo de fundo (top 10):")
        for tipo, count in principais_df['tipo_fundo'].value_counts().head(10).items():
            print(f"  {tipo}: {count:,}")

    if 'situacao' in principais_df.columns:
        print("\nPor situação:")
        for sit, count in principais_df['situacao'].value_counts().items():
            pct = count / len(principais_df) * 100
            print(f"  {sit}: {count:,} ({pct:.1f}%)")

    # Class-level statistics
    if classes_df is not None and not classes_df.empty:
        print(f"\nClasses de cotas: {len(classes_df)}")

        if 'classificacao_anbima' in classes_df.columns:
            anbima_count = classes_df['classificacao_anbima'].notna().sum()
            print(f"  - Com classificação ANBIMA: {anbima_count}")

        if 'classe_esg' in classes_df.columns:
            esg_count = (classes_df['classe_esg'].str.upper() == 'S').sum()
            print(f"  - Com designação ESG: {esg_count}")

        if 'publico_alvo' in classes_df.columns:
            print("\n  Por público-alvo:")
            for pub, count in classes_df['publico_alvo'].value_counts().items():
                print(f"    {pub}: {count:,}")

    # Field coverage in principais
    print("\nCobertura de campos (fundos_principais):")
    coverage_fields = ['classificacao_anbima', 'gestor', 'administrador',
                       'patrimonio_liquido', 'publico_alvo']
    for field in coverage_fields:
        if field in principais_df.columns:
            non_null = principais_df[field].notna().sum()
            pct = (non_null / len(principais_df)) * 100
            print(f"  {field}: {non_null:,} ({pct:.1f}%)")

    print("\n" + "=" * 60)
