"""
Parser for RCVM175 fund registry (registro_fundo_classe.zip)

Parses fund and class data, keeping only essential fields.
"""
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple

from ..config import (
    RCVM175_URL, RCVM175_FILES, CSV_ENCODING, CSV_DELIMITER,
    FUNDO_MAPPING, CLASSE_MAPPING, STATUS_ACTIVE
)
from ..downloader import download_zip


def parse_rcvm175(use_cache: bool = True, force: bool = False) -> Tuple[
    Optional[pd.DataFrame],
    Optional[pd.DataFrame]
]:
    """
    Download and parse RCVM175 fund registry.

    Returns:
        Tuple of (fundos_df, classes_df)
    """
    print("Processando registro de fundos (RCVM175)...")

    extract_dir = download_zip(RCVM175_URL, use_cache=use_cache, force=force)
    if extract_dir is None:
        print("  ✗ Falha ao obter registro_fundo_classe.zip")
        return None, None

    fundos_df = _parse_fundos(extract_dir)
    classes_df = _parse_classes(extract_dir)

    return fundos_df, classes_df


def _parse_fundos(extract_dir: Path) -> Optional[pd.DataFrame]:
    """Parse registro_fundo.csv with field mapping."""
    csv_path = extract_dir / RCVM175_FILES['fundos']
    if not csv_path.exists():
        print(f"  ✗ Arquivo não encontrado: {RCVM175_FILES['fundos']}")
        return None

    df = pd.read_csv(
        csv_path,
        sep=CSV_DELIMITER,
        encoding=CSV_ENCODING,
        low_memory=False,
        dtype=str
    )

    # Apply field mapping
    rename_map = {k: v for k, v in FUNDO_MAPPING.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    # Keep only mapped columns
    keep_cols = [c for c in FUNDO_MAPPING.values() if c in df.columns]
    df = df[keep_cols]

    # Filter only active funds
    df = df[df['situacao'] == STATUS_ACTIVE].copy()

    # Convert numeric fields
    df['patrimonio_liquido'] = _to_float(df.get('patrimonio_liquido'))

    print(f"  ✓ {len(df):,} fundos ativos carregados")

    return df


def _parse_classes(extract_dir: Path) -> Optional[pd.DataFrame]:
    """Parse registro_classe.csv with field mapping (essentials only)."""
    csv_path = extract_dir / RCVM175_FILES['classes']
    if not csv_path.exists():
        print(f"  ✗ Arquivo não encontrado: {RCVM175_FILES['classes']}")
        return None

    df = pd.read_csv(
        csv_path,
        sep=CSV_DELIMITER,
        encoding=CSV_ENCODING,
        low_memory=False,
        dtype=str
    )

    # Apply field mapping
    rename_map = {k: v for k, v in CLASSE_MAPPING.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    # Keep only mapped columns
    keep_cols = [c for c in CLASSE_MAPPING.values() if c in df.columns]
    df = df[keep_cols]

    print(f"  ✓ {len(df):,} classes carregadas")

    return df


def _to_float(series: Optional[pd.Series]) -> Optional[pd.Series]:
    """Convert series to float, handling Brazilian decimal format."""
    if series is None:
        return None
    return pd.to_numeric(
        series.astype(str).str.replace(',', '.'),
        errors='coerce'
    )
