"""
Merger module - Combines fund and class data.

Merges essential class fields (classificacao_anbima, publico_alvo, custodiante)
into the fund table using first non-null aggregation per fund.
"""
import pandas as pd
from typing import Optional

from .config import OUTPUT_COLUMNS_FUNDOS


def merge_fund_with_class(
    fundos_df: pd.DataFrame,
    classes_df: Optional[pd.DataFrame]
) -> pd.DataFrame:
    """
    Merge fund data with class essentials (one row per fund).

    For funds with multiple classes, takes first non-null value for each field.
    """
    result = fundos_df.copy()

    if classes_df is None or classes_df.empty:
        print("  ⚠ Sem dados de classes para mesclar")
        return result

    # Aggregate class data per fund (first non-null for each field)
    class_agg = classes_df.groupby('id_fundo').agg({
        col: 'first' for col in classes_df.columns if col != 'id_fundo'
    }).reset_index()

    # Merge
    result = result.merge(class_agg, on='id_fundo', how='left')

    return result


def prepare_output(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame for output.

    - Select and order columns
    - Format CNPJ as text for Excel (prefix with ')
    """
    # Select output columns
    available_cols = [c for c in OUTPUT_COLUMNS_FUNDOS if c in df.columns]
    result = df[available_cols].copy()

    # Format CNPJ as text for Excel (prefix with apostrophe)
    if 'cnpj' in result.columns:
        result['cnpj'] = "'" + result['cnpj'].astype(str)

    return result
