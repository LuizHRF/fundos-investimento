#!/usr/bin/env python3
"""
Comparador de Fundos de Investimento - CLI

Funções de interface de linha de comando para o sistema de comparação.
"""

import sys
from pathlib import Path
from .analisador_fundos import AnalisadorFundos


def exibir_estatisticas(analisador: AnalisadorFundos):
    """Exibe estatísticas dos fundos"""
    print("\n" + "=" * 70)
    print("ESTATÍSTICAS DOS FUNDOS")
    print("=" * 70)

    stats = analisador.obter_estatisticas()
    print(f"Total de fundos no banco: {stats['total_fundos']}")
    print(f"Fundos ativos (Em Funcionamento Normal): {stats['fundos_ativos']}")

    print(f"\nPor situação:")
    for situacao, qtd in list(stats['por_situacao'].items())[:5]:
        print(f"  {situacao}: {qtd}")

    if stats['por_tipo']:
        print(f"\nFundos ativos por tipo:")
        for tipo, qtd in stats['por_tipo'].items():
            print(f"  {tipo}: {qtd}")

    if stats['maiores_gestores']:
        print(f"\nMaiores gestores (por quantidade de fundos ativos):")
        for gestor in stats['maiores_gestores'][:5]:
            print(f"  {gestor['gestor']}: {gestor['qtd_fundos']} fundos")


def exibir_comparacao(analisador: AnalisadorFundos, lista_cnpj: list):
    """Exibe comparação de fundos"""
    print("\n" + "=" * 70)
    print("COMPARAÇÃO DE FUNDOS")
    print("=" * 70)

    comparacao = analisador.comparar_fundos(lista_cnpj)

    if "erro" in comparacao:
        print(f"Erro: {comparacao['erro']}")
        return

    print(f"Data da comparação: {comparacao['data_comparacao']}")
    print(f"Fundos comparados: {len(comparacao['fundos'])}")

    for categoria, campos in comparacao['campos'].items():
        print(f"\n{categoria}:")
        print("-" * 70)
        for campo in campos:
            print(f"\n  {campo.upper().replace('_', ' ')}:")
            for i, fundo in enumerate(comparacao['fundos'], 1):
                valor = fundo.get(campo, 'N/A')
                if valor is None:
                    valor = 'N/A'
                elif campo == 'patrimonio_liquido' and valor != 'N/A':
                    valor = f"R$ {valor:,.2f}"
                elif campo in ['taxa_admin', 'taxa_performance'] and valor != 'N/A':
                    valor = f"{valor}%"
                print(f"    Fundo {i}: {valor}")


def exibir_mudancas(analisador: AnalisadorFundos, limite: int = 10):
    """Exibe mudanças recentes"""
    print("\n" + "=" * 70)
    print("MUDANÇAS RECENTES DETECTADAS")
    print("=" * 70)

    mudancas = analisador.banco.obter_mudancas(limite=limite)

    if not mudancas:
        print("Nenhuma mudança detectada ainda.")
        print("As mudanças serão registradas após atualizações nos dados.")
        return

    print(f"Últimas {len(mudancas)} mudanças:\n")
    for m in mudancas:
        print(f"CNPJ: {m['cnpj']}")
        print(f"  Campo: {m['campo']}")
        print(f"  Anterior: {m['valor_anterior']}")
        print(f"  Novo: {m['valor_novo']}")
        print(f"  Data: {m['alterado_em']}")
        print()


def demonstracao_completa(caminho_db: str = './output/fundos.db', diretorio_cache: str = './output/cache'):
    """Executa demonstração completa do sistema"""
    print("=" * 70)
    print("SISTEMA DE COMPARAÇÃO DE FUNDOS DE INVESTIMENTO")
    print("Dados: Portal de Dados Abertos da CVM")
    print("=" * 70)

    db_path = Path(caminho_db)

    analisador = AnalisadorFundos(
        caminho_db=caminho_db,
        diretorio_cache=diretorio_cache
    )

    if not db_path.exists():
        print("\nBanco de dados não encontrado. Carregando dados da CVM...")
        print("Isso pode levar alguns minutos na primeira execução...\n")
        analisador.carregar_dados()
    else:
        print("\nUsando banco de dados existente.")
        print("Para atualizar, execute: python main.py comparar --carregar\n")

    exibir_estatisticas(analisador)

    print("\n" + "=" * 70)
    print("BUSCANDO FUNDOS ATIVOS...")
    print("=" * 70)

    fundos_ativos = analisador.banco.buscar_fundos({
        'situacao': 'EM FUNCIONAMENTO NORMAL'
    })
    print(f"Encontrados {len(fundos_ativos)} fundos ativos")

    if len(fundos_ativos) >= 2:
        print("\nPrimeiros 5 fundos ativos:")
        for fundo in fundos_ativos[:5]:
            print(f"\n  Nome: {fundo['nome']}")
            print(f"  CNPJ: {fundo['cnpj']}")
            print(f"  Tipo: {fundo['tipo_fundo']}")
            print(f"  Classe ANBIMA: {fundo['classe_anbima']}")
            print(f"  Gestor: {fundo['gestor']}")
            if fundo['taxa_admin']:
                print(f"  Taxa Admin: {fundo['taxa_admin']}%")
            if fundo['patrimonio_liquido']:
                print(f"  Patrimônio Líquido: R$ {fundo['patrimonio_liquido']:,.2f}")

        print("\n" + "=" * 70)
        print("EXEMPLO: Comparando 2 fundos ativos...")
        lista_cnpj = [fundos_ativos[0]['cnpj'], fundos_ativos[1]['cnpj']]
        exibir_comparacao(analisador, lista_cnpj)

        arquivo_saida = './output/comparacao_exemplo.csv'
        print(f"\nExportando comparação para {arquivo_saida}...")
        analisador.exportar_comparacao_csv(lista_cnpj, arquivo_saida)

    exibir_mudancas(analisador)

    print("\n" + "=" * 70)
    print("DEMONSTRAÇÃO CONCLUÍDA")
    print("=" * 70)
    print("\nPróximos passos:")
    print("  - Use 'python main.py comparar --buscar' para buscar fundos específicos")
    print("  - Use a classe AnalisadorFundos diretamente em seu código")
    print("  - Veja a documentação em README.md")


def main_comparador(args: list = None):
    """Função principal do comparador de fundos"""
    if args is None:
        args = sys.argv[1:]

    caminho_db = './output/fundos.db'
    diretorio_cache = './output/cache'

    if len(args) > 0:
        if args[0] == '--carregar':
            print("Carregando/atualizando dados da CVM...")
            analisador = AnalisadorFundos(
                caminho_db=caminho_db,
                diretorio_cache=diretorio_cache
            )
            analisador.carregar_dados()
            print("\nDados carregados com sucesso!")

        elif args[0] == '--stats':
            analisador = AnalisadorFundos(
                caminho_db=caminho_db,
                diretorio_cache=diretorio_cache
            )
            exibir_estatisticas(analisador)

        elif args[0] in ['--help', '-h']:
            print(__doc__)
            print("\nOpções disponíveis:")
            print("  --carregar   Carregar/atualizar dados da CVM")
            print("  --stats      Mostrar apenas estatísticas")
            print("  --help, -h   Mostrar esta ajuda")

        else:
            print(f"Opção desconhecida: {args[0]}")
            print("Use --help para ver opções disponíveis")

    else:
        demonstracao_completa(caminho_db, diretorio_cache)


if __name__ == "__main__":
    main_comparador()
