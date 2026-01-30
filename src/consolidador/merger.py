"""
Merger module - Combines RCVM175 fund, class, and subclass data.

Handles the three-table hierarchy:
- REGISTRO_FUNDO → fundos_principais.csv (one row per fund)
- REGISTRO_CLASSE → fundos_classes.csv (one row per class)
"""
import pandas as pd
from typing import Optional

from .config import OUTPUT_COLUMNS_PRINCIPAIS, OUTPUT_COLUMNS_CLASSES


def merge_fund_with_primary_class(
    fundos_df: pd.DataFrame,
    classes_df: Optional[pd.DataFrame]
) -> pd.DataFrame:
    """
    Merge fund data with primary class data for fundos_principais.csv.

    For funds with multiple classes, aggregates class-level fields:
    - classificacao_anbima: from first class (or most common)
    - classe_esg: True if any class has ESG
    - publico_alvo: most restrictive (Profissional > Qualificado > Público Geral)
    - taxa_administracao: from first class

    Args:
        fundos_df: Fund data from REGISTRO_FUNDO.CSV
        classes_df: Class data from REGISTRO_CLASSE.CSV

    Returns:
        Merged DataFrame with one row per fund
    """
    result = fundos_df.copy()

    if classes_df is None or classes_df.empty:
        print("  ⚠ Sem dados de classes para mesclar")
        return result

    # Aggregate class data per fund
    class_agg = _aggregate_classes_per_fund(classes_df)

    # Merge aggregated class data
    result = result.merge(
        class_agg,
        on='id_fundo',
        how='left',
        suffixes=('', '_classe')
    )

    # Fill missing values from class data
    for col in ['classificacao_anbima', 'publico_alvo', 'forma_condominio',
                'classe_esg', 'exclusivo']:
        if f'{col}_classe' in result.columns:
            if col in result.columns:
                result[col] = result[col].fillna(result[f'{col}_classe'])
            else:
                result[col] = result[f'{col}_classe']
            result = result.drop(columns=[f'{col}_classe'])

    return result


def _aggregate_classes_per_fund(classes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate class-level data to fund level.

    For funds with multiple classes:
    - Take first non-null classificacao_anbima
    - classe_esg: 'S' if any class has it
    - publico_alvo: most restrictive tier
    - Taxa: from first class
    """
    # Priority order for publico_alvo (most restrictive first)
    publico_priority = {
        'Profissional': 1,
        'Qualificado': 2,
        'Público Geral': 3,
    }

    def agg_publico_alvo(series):
        """Return most restrictive publico_alvo."""
        valid = series.dropna()
        if valid.empty:
            return None
        priorities = valid.map(lambda x: publico_priority.get(x, 99))
        return valid.iloc[priorities.argmin()]

    def agg_esg(series):
        """Return 'S' if any class has ESG."""
        if series.str.upper().eq('S').any():
            return 'S'
        return None

    def first_non_null(series):
        """Return first non-null value."""
        valid = series.dropna()
        return valid.iloc[0] if not valid.empty else None

    agg_funcs = {
        'classificacao_anbima': first_non_null,
        'forma_condominio': first_non_null,
        'exclusivo': first_non_null,
    }

    # Only add columns that exist
    agg_dict = {k: v for k, v in agg_funcs.items() if k in classes_df.columns}

    if 'publico_alvo' in classes_df.columns:
        agg_dict['publico_alvo'] = agg_publico_alvo

    if 'classe_esg' in classes_df.columns:
        agg_dict['classe_esg'] = agg_esg

    if not agg_dict:
        return pd.DataFrame(columns=['id_fundo'])

    result = classes_df.groupby('id_fundo').agg(agg_dict).reset_index()
    return result


def prepare_principais_output(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame for fundos_principais.csv output.

    Reorders columns according to OUTPUT_COLUMNS_PRINCIPAIS.
    """
    # Select only columns defined in output schema
    available_cols = [c for c in OUTPUT_COLUMNS_PRINCIPAIS if c in df.columns]

    result = df[available_cols].copy()
    return result


def prepare_classes_output(
    fundos_df: pd.DataFrame,
    classes_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Prepare DataFrame for fundos_classes.csv output.

    Joins fund CNPJ to each class for linking.
    """
    if classes_df is None or classes_df.empty:
        return pd.DataFrame()

    # Get CNPJ from fundos for joining
    fund_cnpj = fundos_df[['id_fundo', 'cnpj']].drop_duplicates()

    # Merge CNPJ to classes
    result = classes_df.merge(fund_cnpj, on='id_fundo', how='left')

    # Select output columns
    available_cols = [c for c in OUTPUT_COLUMNS_CLASSES if c in result.columns]
    result = result[available_cols]

    return result
