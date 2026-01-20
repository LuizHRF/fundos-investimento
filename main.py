#!/usr/bin/env python3
"""
CVM Fundos de Investimento - Ferramenta Unificada

Sistema para monitoramento e comparação de fundos de investimento brasileiros
usando dados do Portal de Dados Abertos da CVM.

Uso:
    python main.py                     # Comparador de fundos (padrão)
    python main.py comparar [opções]   # Comparador de fundos
    python main.py dashboard [opções]  # Dashboard de monitoramento

Opções do comparador:
    --carregar   Carregar/atualizar dados da CVM
    --stats      Mostrar apenas estatísticas
    --help       Mostrar ajuda

Opções do dashboard:
    --listar       Listar todos os datasets
    --busca TERMO  Buscar datasets por termo
    --recentes     Mostrar recursos mais recentes
    --help         Mostrar ajuda

Exemplos:
    python main.py                          # Executar comparador
    python main.py comparar --carregar      # Atualizar dados do comparador
    python main.py dashboard                # Executar dashboard
    python main.py dashboard --busca FII    # Buscar datasets de FII
"""

import sys
from pathlib import Path

# Adicionar diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src import main_comparador, main_dashboard


def exibir_ajuda():
    """Exibe ajuda geral"""
    print(__doc__)


def main():
    """Função principal unificada"""
    if len(sys.argv) < 2:
        # Padrão: executar comparador de fundos
        main_comparador([])
        return

    comando = sys.argv[1].lower()

    if comando in ['--help', '-h', 'help']:
        exibir_ajuda()

    elif comando in ['comparar', 'compare', 'c']:
        # Comparador de fundos
        main_comparador(sys.argv[2:])

    elif comando in ['dashboard', 'dash', 'd']:
        # Dashboard de monitoramento
        main_dashboard(sys.argv[2:])

    elif comando.startswith('--'):
        # Se passa opções diretamente, assume comparador
        main_comparador(sys.argv[1:])

    else:
        print(f"Comando desconhecido: {comando}")
        print("\nComandos disponíveis:")
        print("  comparar   Comparador de fundos (padrão)")
        print("  dashboard  Dashboard de monitoramento")
        print("  --help     Mostrar ajuda")
        sys.exit(1)


if __name__ == "__main__":
    main()
