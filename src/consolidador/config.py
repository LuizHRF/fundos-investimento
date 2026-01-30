"""
Configuration for CVM Fund Data Consolidation System

Based on CVM Resolution 175 (2023) - New fund registration framework.
Uses registro_fundo_classe.zip as primary data source.
"""
from pathlib import Path

# Base URLs
BASE_URL = "https://dados.cvm.gov.br/dados"

# Primary data source (RCVM175 - 33,475 active funds)
RCVM175_URL = f"{BASE_URL}/FI/CAD/DADOS/registro_fundo_classe.zip"

# CSV parsing settings (CVM standard)
CSV_ENCODING = 'latin-1'
CSV_DELIMITER = ';'

# Output settings
OUTPUT_ENCODING = 'utf-8-sig'  # BOM for Excel compatibility
OUTPUT_DIR = Path("./output")
CACHE_DIR = Path("./output/cache")

# RCVM175 file names inside ZIP (lowercase)
RCVM175_FILES = {
    'fundos': 'registro_fundo.csv',
    'classes': 'registro_classe.csv',
    'subclasses': 'registro_subclasse.csv',
}

# Field mapping: registro_fundo.csv -> output
# Based on actual column names from CVM file
FUNDO_MAPPING = {
    'ID_Registro_Fundo': 'id_fundo',
    'CNPJ_Fundo': 'cnpj',
    'Codigo_CVM': 'codigo_cvm',
    'Denominacao_Social': 'nome_fundo',
    'Tipo_Fundo': 'tipo_fundo',
    'Situacao': 'situacao',
    'Data_Registro': 'data_registro',
    'Data_Constituicao': 'data_constituicao',
    'Data_Cancelamento': 'data_cancelamento',
    'Data_Adaptacao_RCVM175': 'data_adaptacao_rcvm175',
    'Patrimonio_Liquido': 'patrimonio_liquido',
    'Data_Patrimonio_Liquido': 'data_patrimonio_liquido',
    'Administrador': 'administrador',
    'CNPJ_Administrador': 'cnpj_administrador',
    'Gestor': 'gestor',
    'CPF_CNPJ_Gestor': 'cnpj_gestor',
    'Tipo_Pessoa_Gestor': 'tipo_pessoa_gestor',
    'Diretor': 'diretor',
}

# Field mapping: registro_classe.csv -> output
# Note: Taxa fields are NOT in this file (disclosed in other documents)
CLASSE_MAPPING = {
    'ID_Registro_Classe': 'id_classe',
    'ID_Registro_Fundo': 'id_fundo',
    'CNPJ_Classe': 'cnpj_classe',
    'Codigo_CVM': 'codigo_cvm_classe',
    'Denominacao_Social': 'nome_classe',
    'Tipo_Classe': 'tipo_classe',
    'Situacao': 'situacao_classe',
    'Classificacao': 'classificacao',
    'Classificacao_Anbima': 'classificacao_anbima',
    'Classe_ESG': 'classe_esg',
    'Forma_Condominio': 'forma_condominio',
    'Publico_Alvo': 'publico_alvo',
    'Exclusivo': 'exclusivo',
    'Indicador_Desempenho': 'indicador_desempenho',
    'Classe_Cotas': 'classe_cotas',
    'Tributacao_Longo_Prazo': 'tributacao_longo_prazo',
    'Entidade_Investimento': 'entidade_investimento',
    'Permitido_Aplicacao_CemPorCento_Exterior': 'permite_100pct_exterior',
    'Patrimonio_Liquido': 'patrimonio_liquido_classe',
    'Data_Patrimonio_Liquido': 'data_patrimonio_liquido_classe',
    'Auditor': 'auditor',
    'CNPJ_Auditor': 'cnpj_auditor',
    'Custodiante': 'custodiante',
    'CNPJ_Custodiante': 'cnpj_custodiante',
    'Controlador': 'controlador',
    'CNPJ_Controlador': 'cnpj_controlador',
}

# Field mapping: registro_subclasse.csv -> output
SUBCLASSE_MAPPING = {
    'ID_Subclasse': 'id_subclasse',
    'ID_Registro_Classe': 'id_classe',
    'Denominacao_Social': 'nome_subclasse',
    'Publico_Alvo': 'publico_alvo_subclasse',
    'Indicador_Previdencia': 'indicador_previdencia',
    'Indicador_INR': 'indicador_inr',
}

# Output column order for fundos_principais.csv
OUTPUT_COLUMNS_PRINCIPAIS = [
    'cnpj',
    'nome_fundo',
    'tipo_fundo',
    'situacao',
    'em_funcionamento',
    'gestor',
    'administrador',
    'patrimonio_liquido',
    'classificacao_anbima',
    'classe_esg',
    'publico_alvo',
    'forma_condominio',
    'exclusivo',
    'data_registro',
    'data_adaptacao_rcvm175',
    'codigo_cvm',
    'cnpj_gestor',
    'cnpj_administrador',
]

# Output column order for fundos_classes.csv
OUTPUT_COLUMNS_CLASSES = [
    'cnpj',
    'cnpj_classe',
    'nome_classe',
    'tipo_classe',
    'situacao_classe',
    'classificacao_anbima',
    'classe_esg',
    'publico_alvo',
    'forma_condominio',
    'exclusivo',
    'patrimonio_liquido_classe',
    'auditor',
    'custodiante',
]

# Fund status values
STATUS_ACTIVE = 'Em Funcionamento Normal'
STATUS_VALUES = [
    'Em Funcionamento Normal',
    'Fase Pré-Operacional',
    'Em Análise',
    'Em Situação Especial',
    'Em Liquidação',
    'Incorporação',
    'Cancelado',
]

# ANBIMA Classification categories (top 10 most common)
ANBIMA_TOP_CATEGORIES = [
    'Multimercados Invest. no Exterior',
    'Multimercados Livre',
    'Renda Fixa Duração Livre Crédito Livre',
    'Previdência Multimercado Livre',
    'Ações Livre',
    'Renda Fixa Duração Baixa Grau Invest.',
    'Previdência Renda Fixa Duração Livre Crédito Livre',
    'Ações Invest. no Exterior',
    'Multimercados Macro',
    'Previdência Renda Fixa Duração Baixa Grau Invest.',
]
