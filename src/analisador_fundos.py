"""
Analisador de Fundos CVM - Gera tabela comparativa de todos os fundos
"""
import pandas as pd
from pathlib import Path

BASE_URL = "https://dados.cvm.gov.br/dados"
CACHE_DIR = Path("./output/cache")
OUTPUT_DIR = Path("./output")

# Colunas para exportação (nome_original: nome_exibição)
COLUNAS_EXPORTAR = {
    'CNPJ_FUNDO': 'CNPJ',
    'DENOM_SOCIAL': 'Nome',
    'TP_FUNDO': 'Tipo',
    'SIT': 'Situação',
    'CLASSE_ANBIMA': 'Classe ANBIMA',
    'CLASSE': 'Classe',
    'PUBLICO_ALVO': 'Público Alvo',
    'GESTOR': 'Gestor',
    'ADMIN': 'Administrador',
    'TAXA_ADM': 'Taxa Admin (%)',
    'TAXA_PERFM': 'Taxa Performance (%)',
    'VL_PATRIM_LIQ': 'Patrimônio Líquido (R$)',
    'DT_PATRIM_LIQ': 'Data Patrimônio',
    'DT_REG': 'Data Registro',
    'FUNDO_EXCLUSIVO': 'Exclusivo',
    'CONDOM': 'Condomínio',
    'RENTAB_FUNDO': 'Rentabilidade',
}


def baixar_csv(url: str, usar_cache: bool = True) -> pd.DataFrame:
    """Baixa CSV da CVM e retorna DataFrame"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / url.split('/')[-1]

    if usar_cache and cache_file.exists():
        return pd.read_csv(cache_file, sep=';', encoding='latin-1', low_memory=False)

    print(f"Baixando: {url}")
    df = pd.read_csv(url, sep=';', encoding='latin-1', low_memory=False)
    df.to_csv(cache_file, sep=';', index=False, encoding='latin-1')
    return df


def carregar_fundos(apenas_ativos: bool = False) -> pd.DataFrame:
    """Carrega dados de todos os fundos da CVM"""
    # Baixar dados cadastrais
    df = baixar_csv(f"{BASE_URL}/FI/CAD/DADOS/cad_fi.csv")

    # Filtrar apenas ativos se solicitado
    if apenas_ativos:
        df = df[df['SIT'] == 'EM FUNCIONAMENTO NORMAL']

    # Converter taxas para float
    for col in ['TAXA_ADM', 'TAXA_PERFM', 'VL_PATRIM_LIQ']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

    return df


def gerar_comparacao(modo: str = 'ativos', arquivo_saida: str = None) -> pd.DataFrame:
    """
    Gera tabela comparativa de todos os fundos

    Args:
        modo: 'ativos' (apenas ativos), 'todos' (exceto cancelados), 'cancelados' (todos)
        arquivo_saida: Caminho para exportar CSV (opcional)

    Returns:
        DataFrame com a comparação
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = carregar_fundos(apenas_ativos=False)

    # Filtrar conforme modo
    if modo == 'ativos':
        df = df[df['SIT'] == 'EM FUNCIONAMENTO NORMAL']
    elif modo == 'todos':
        df = df[df['SIT'] != 'CANCELADA']

    # Selecionar e renomear colunas disponíveis
    colunas_disponiveis = [c for c in COLUNAS_EXPORTAR.keys() if c in df.columns]
    df_export = df[colunas_disponiveis].copy()
    df_export.columns = [COLUNAS_EXPORTAR[c] for c in colunas_disponiveis]

    # Ordenar: ativos primeiro, depois por patrimônio
    if modo != 'ativos':
        ordem_situacao = {'EM FUNCIONAMENTO NORMAL': 0, 'FASE PRÉ-OPERACIONAL': 1,
                         'EM ANÁLISE': 2, 'EM SITUAÇÃO ESPECIAL': 3, 'LIQUIDAÇÃO': 4,
                         'INCORPORAÇÃO': 5, 'CANCELADA': 6}
        df_export['_ordem'] = df_export['Situação'].map(ordem_situacao).fillna(99)
        df_export = df_export.sort_values(['_ordem', 'Patrimônio Líquido (R$)'],
                                          ascending=[True, False], na_position='last')
        df_export = df_export.drop('_ordem', axis=1)
    elif 'Patrimônio Líquido (R$)' in df_export.columns:
        df_export = df_export.sort_values('Patrimônio Líquido (R$)', ascending=False, na_position='last')

    # Exportar
    if arquivo_saida is None:
        arquivo_saida = OUTPUT_DIR / "comparacao_fundos.csv"

    df_export.to_csv(arquivo_saida, index=False, encoding='utf-8-sig')
    print(f"✓ {len(df_export)} fundos exportados para {arquivo_saida}")

    return df_export


def exibir_estatisticas(df: pd.DataFrame = None):
    """Exibe estatísticas dos fundos"""
    if df is None:
        df = carregar_fundos()

    print("\n" + "=" * 60)
    print("ESTATÍSTICAS DOS FUNDOS CVM")
    print("=" * 60)

    print(f"\nTotal de fundos: {len(df)}")

    ativos = df[df['SIT'] == 'EM FUNCIONAMENTO NORMAL']
    print(f"Fundos ativos: {len(ativos)}")

    print("\nPor situação:")
    for sit, qtd in df['SIT'].value_counts().head(5).items():
        print(f"  {sit}: {qtd}")

    print("\nPor tipo (ativos):")
    for tipo, qtd in ativos['TP_FUNDO'].value_counts().items():
        print(f"  {tipo}: {qtd}")

    if 'CLASSE_ANBIMA' in ativos.columns:
        print("\nTop 10 Classes ANBIMA (ativos):")
        for classe, qtd in ativos['CLASSE_ANBIMA'].value_counts().head(10).items():
            if pd.notna(classe):
                print(f"  {classe}: {qtd}")

    if 'VL_PATRIM_LIQ' in ativos.columns:
        pl_total = ativos['VL_PATRIM_LIQ'].sum()
        print(f"\nPatrimônio líquido total: R$ {pl_total:,.2f}")


def main(modo: str = 'ativos'):
    """Executa análise completa"""
    print("=" * 60)
    print("COMPARAÇÃO DE FUNDOS DE INVESTIMENTO CVM")
    print("=" * 60)

    # Carregar e mostrar estatísticas
    df = carregar_fundos()
    exibir_estatisticas(df)

    # Gerar arquivo de comparação
    modo_desc = {'ativos': 'apenas ativos', 'todos': 'exceto cancelados', 'cancelados': 'todos'}
    print(f"\nGerando tabela ({modo_desc.get(modo, modo)})...")
    gerar_comparacao(modo=modo)

    print("\n" + "=" * 60)
    print("Arquivo gerado: output/comparacao_fundos.csv")
    print("=" * 60)


if __name__ == "__main__":
    main()
