"""
Main consolidator - Orchestrates the consolidation pipeline.

Outputs:
- fundos.csv: Active funds with class essentials
- composicao_carteira.xlsx: Portfolio composition with one sheet per month
"""
from pathlib import Path
from typing import Tuple, Optional

from .parsers import parse_rcvm175, parse_cda_multiple
from .merger import merge_fund_with_class, prepare_output
from .exporter import export_fundos, export_carteira_excel, print_summary


def consolidate(force: bool = False) -> Tuple[Path, Optional[Path]]:
    """
    Run the consolidation pipeline.

    1. Parse fund registry (RCVM175) - active funds only
    2. Merge with class essentials (ANBIMA, público-alvo, custodiante)
    3. Parse portfolio composition (CDA) - multiple months
    4. Export fundos.csv and composicao_carteira.xlsx

    Args:
        force: Force re-download of all files

    Returns:
        Tuple of (fundos_path, carteira_path)
    """
    print("=" * 50)
    print("CONSOLIDAÇÃO DE FUNDOS CVM")
    print("=" * 50)

    use_cache = not force

    # Step 1: Parse fund registry
    fundos_df, classes_df = parse_rcvm175(use_cache=use_cache, force=force)

    if fundos_df is None:
        raise RuntimeError("Falha ao carregar registro de fundos!")

    # Step 2: Merge fund with class data
    print("\nMesclando dados...")
    merged_df = merge_fund_with_class(fundos_df, classes_df)
    output_df = prepare_output(merged_df)

    # Step 3: Parse portfolio composition (CDA) - multiple months
    carteira_data = parse_cda_multiple(use_cache=use_cache, force=force)

    # Step 4: Export
    fundos_path = export_fundos(output_df)
    carteira_path = export_carteira_excel(carteira_data)

    # Summary
    print_summary(output_df, carteira_data)

    return fundos_path, carteira_path
