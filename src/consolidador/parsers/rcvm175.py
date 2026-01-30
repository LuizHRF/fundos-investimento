"""
Parser for RCVM175 fund registry (registro_fundo_classe.zip)

CVM Resolution 175 (2023) introduced a three-table hierarchical structure:
- REGISTRO_FUNDO.CSV: Fund-level data (86,878 records)
- REGISTRO_CLASSE.CSV: Share class data (35,411 records)
- REGISTRO_SUBCLASSE.CSV: Subclass data (6,615 records)
"""
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict

from ..config import (
    RCVM175_URL, RCVM175_FILES, CSV_ENCODING, CSV_DELIMITER,
    FUNDO_MAPPING, CLASSE_MAPPING, SUBCLASSE_MAPPING, STATUS_ACTIVE
)
from ..downloader import download_zip


def parse_rcvm175(use_cache: bool = True, force: bool = False) -> Tuple[
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    Optional[pd.DataFrame]
]:
    """
    Download and parse RCVM175 fund registry ZIP file.

    Returns:
        Tuple of (fundos_df, classes_df, subclasses_df)
    """
    print("Processando registro RCVM175 (registro_fundo_classe.zip)...")

    extract_dir = download_zip(RCVM175_URL, use_cache=use_cache, force=force)
    if extract_dir is None:
        print("  ✗ Falha ao obter registro_fundo_classe.zip - arquivo obrigatório!")
        return None, None, None

    # Parse each CSV file
    fundos_df = _parse_fundos(extract_dir)
    classes_df = _parse_classes(extract_dir)
    subclasses_df = _parse_subclasses(extract_dir)

    return fundos_df, classes_df, subclasses_df


def _parse_fundos(extract_dir: Path) -> Optional[pd.DataFrame]:
    """Parse REGISTRO_FUNDO.CSV with field mapping."""
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

    print(f"  ✓ {len(df)} fundos carregados")

    # Apply field mapping
    rename_map = {k: v for k, v in FUNDO_MAPPING.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    # Derive em_funcionamento boolean
    df['em_funcionamento'] = (df['situacao'] == STATUS_ACTIVE)

    # Convert numeric fields
    df['patrimonio_liquido'] = _to_float(df.get('patrimonio_liquido'))

    # Statistics
    active_count = df['em_funcionamento'].sum()
    print(f"  ✓ {active_count} fundos em funcionamento normal")

    return df


def _parse_classes(extract_dir: Path) -> Optional[pd.DataFrame]:
    """Parse REGISTRO_CLASSE.CSV with field mapping."""
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

    print(f"  ✓ {len(df)} classes de cotas carregadas")

    # Apply field mapping
    rename_map = {k: v for k, v in CLASSE_MAPPING.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    # Convert numeric fields
    df['patrimonio_liquido_classe'] = _to_float(df.get('patrimonio_liquido_classe'))
    df['taxa_administracao'] = _to_float(df.get('taxa_administracao'))
    df['taxa_performance'] = _to_float(df.get('taxa_performance'))

    # ESG statistics (count only 'S' values, not empty strings)
    if 'classe_esg' in df.columns:
        esg_count = (df['classe_esg'].str.upper() == 'S').sum()
        if esg_count > 0:
            print(f"  ✓ {esg_count} classes com designação ESG")

    return df


def _parse_subclasses(extract_dir: Path) -> Optional[pd.DataFrame]:
    """Parse REGISTRO_SUBCLASSE.CSV with field mapping."""
    csv_path = extract_dir / RCVM175_FILES['subclasses']
    if not csv_path.exists():
        print(f"  ⚠ Arquivo não encontrado: {RCVM175_FILES['subclasses']}")
        return None

    df = pd.read_csv(
        csv_path,
        sep=CSV_DELIMITER,
        encoding=CSV_ENCODING,
        low_memory=False,
        dtype=str
    )

    print(f"  ✓ {len(df)} subclasses carregadas")

    # Apply field mapping
    rename_map = {k: v for k, v in SUBCLASSE_MAPPING.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    return df


def _to_float(series: Optional[pd.Series]) -> Optional[pd.Series]:
    """Convert series to float, handling Brazilian decimal format."""
    if series is None:
        return None
    return pd.to_numeric(
        series.astype(str).str.replace(',', '.'),
        errors='coerce'
    )


def get_fund_summary(fundos_df: pd.DataFrame) -> Dict:
    """Generate summary statistics for parsed funds."""
    summary = {
        'total_fundos': len(fundos_df),
        'ativos': fundos_df['em_funcionamento'].sum() if 'em_funcionamento' in fundos_df.columns else 0,
    }

    if 'tipo_fundo' in fundos_df.columns:
        summary['por_tipo'] = fundos_df['tipo_fundo'].value_counts().to_dict()

    if 'situacao' in fundos_df.columns:
        summary['por_situacao'] = fundos_df['situacao'].value_counts().to_dict()

    return summary
