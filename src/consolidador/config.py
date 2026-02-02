"""
Configuration for CVM Fund Data Consolidation System

Based on CVM Resolution 175 (2023) - New fund registration framework.
Outputs:
- fundos.csv: Fund registry + class essentials (one row per fund)
- composicao_carteira.csv: Portfolio composition (multiple rows per fund)
"""
from pathlib import Path
from datetime import datetime

# Base URLs
BASE_URL = "https://dados.cvm.gov.br/dados"

# Primary data source (RCVM175 - fund registry)
RCVM175_URL = f"{BASE_URL}/FI/CAD/DADOS/registro_fundo_classe.zip"

# Portfolio composition data (CDA - Composição e Diversificação das Aplicações)
CDA_URL_TEMPLATE = f"{BASE_URL}/FI/DOC/CDA/DADOS/cda_fi_{{yyyymm}}.zip"

# CSV parsing settings (CVM standard)
CSV_ENCODING = 'latin-1'
CSV_DELIMITER = ';'

# Output settings
OUTPUT_ENCODING = 'utf-8-sig'  # BOM for Excel compatibility
OUTPUT_DIR = Path("./output")
CACHE_DIR = Path("./output/cache")

# RCVM175 file names inside ZIP
RCVM175_FILES = {
    'fundos': 'registro_fundo.csv',
    'classes': 'registro_classe.csv',
}

# CDA file patterns inside ZIP
CDA_FILES = {
    'titulos_publicos': 'cda_fi_BLC_1_{yyyymm}.csv',
    'cotas_fundos': 'cda_fi_BLC_2_{yyyymm}.csv',
    'swap': 'cda_fi_BLC_3_{yyyymm}.csv',
    'acoes': 'cda_fi_BLC_4_{yyyymm}.csv',
    'titulos_privados': 'cda_fi_BLC_5_{yyyymm}.csv',
    'derivativos': 'cda_fi_BLC_6_{yyyymm}.csv',
    'investimento_exterior': 'cda_fi_BLC_7_{yyyymm}.csv',
    'demais_ativos': 'cda_fi_BLC_8_{yyyymm}.csv',
}

# Field mapping: registro_fundo.csv -> output
FUNDO_MAPPING = {
    'ID_Registro_Fundo': 'id_fundo',
    'CNPJ_Fundo': 'cnpj',
    'Denominacao_Social': 'nome_fundo',
    'Tipo_Fundo': 'tipo_fundo',
    'Situacao': 'situacao',
    'Patrimonio_Liquido': 'patrimonio_liquido',
    'Administrador': 'administrador',
    'Gestor': 'gestor',
}

# Field mapping: registro_classe.csv -> output (essentials + custodiante)
CLASSE_MAPPING = {
    'ID_Registro_Fundo': 'id_fundo',
    'Classificacao_Anbima': 'classificacao_anbima',
    'Publico_Alvo': 'publico_alvo',
    'Custodiante': 'custodiante',
}

# Field mapping: CDA files -> output
CDA_MAPPING = {
    'CNPJ_FUNDO_CLASSE': 'cnpj',
    'TP_APLIC': 'tipo_aplicacao',
    'TP_ATIVO': 'tipo_ativo',
    'DS_ATIVO': 'descricao_ativo',
    'EMISSOR': 'emissor',
    'VL_MERC_POS_FINAL': 'valor_mercado',
    'QT_POS_FINAL': 'quantidade',
    'DT_COMPTC': 'data_competencia',
}

# Output columns for fundos.csv (one row per fund)
OUTPUT_COLUMNS_FUNDOS = [
    'cnpj',
    'nome_fundo',
    'tipo_fundo',
    'gestor',
    'administrador',
    'custodiante',
    'patrimonio_liquido',
    'classificacao_anbima',
    'publico_alvo',
]

# Output columns for composicao_carteira.csv (multiple rows per fund)
OUTPUT_COLUMNS_CARTEIRA = [
    'cnpj',
    'tipo_aplicacao',
    'tipo_ativo',
    'descricao_ativo',
    'emissor',
    'valor_mercado',
    'quantidade',
    'data_competencia',
]

# Fund status
STATUS_ACTIVE = 'Em Funcionamento Normal'


def get_latest_cda_period():
    """Return YYYYMM for most recent likely available CDA data."""
    today = datetime.now()
    # CDA is typically available 2 months behind
    # (e.g., in Feb 2026, Dec 2025 is the latest available)
    if today.month <= 2:
        return f"{today.year - 1}12"
    else:
        return f"{today.year}{today.month - 2:02d}"
