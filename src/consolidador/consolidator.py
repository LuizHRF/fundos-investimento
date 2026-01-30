"""
Main consolidator - Orchestrates the RCVM175 consolidation pipeline.

Based on CVM Resolution 175 (2023), this module consolidates fund data from
the three-table hierarchy into comprehensive CSV outputs.
"""
from typing import Tuple
from pathlib import Path

from .parsers import parse_rcvm175
from .merger import merge_fund_with_primary_class, prepare_principais_output, prepare_classes_output
from .exporter import export_principais, export_classes, print_summary


def consolidate(months: int = 6, force: bool = False) -> Tuple[Path, Path]:
    """
    Run the full RCVM175 consolidation pipeline.

    Pipeline steps:
    1. Download and parse registro_fundo_classe.zip
    2. Parse three CSV tables (fundos, classes, subclasses)
    3. Merge fund data with primary class data
    4. Export to fundos_principais.csv and fundos_classes.csv

    Args:
        months: (Unused in RCVM175 - kept for API compatibility)
        force: Force re-download of all files

    Returns:
        Tuple of (principais_path, classes_path)
    """
    print("=" * 60)
    print("CONSOLIDAÇÃO DE DADOS DE FUNDOS CVM (RCVM175)")
    print("=" * 60)
    print(f"\nFonte: registro_fundo_classe.zip")
    print(f"Forçar re-download: {'Sim' if force else 'Não'}")
    print()

    use_cache = not force

    # Step 1: Parse RCVM175 data (three tables)
    fundos_df, classes_df, subclasses_df = parse_rcvm175(
        use_cache=use_cache, force=force
    )

    if fundos_df is None:
        raise RuntimeError("Falha ao carregar registro_fundo_classe.zip - arquivo obrigatório!")

    # Step 2: Merge fund data with class data
    print("\nConsolidando dados...")
    merged_df = merge_fund_with_primary_class(fundos_df, classes_df)

    # Step 3: Prepare output formats
    principais_df = prepare_principais_output(merged_df)
    classes_output_df = prepare_classes_output(fundos_df, classes_df)

    # Step 4: Export
    principais_path = export_principais(principais_df)
    classes_path = export_classes(classes_output_df)

    # Summary
    print_summary(principais_df, classes_output_df)

    return principais_path, classes_path
