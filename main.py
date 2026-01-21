#!/usr/bin/env python3
"""
CVM Fundos de Investimento

Uso:
    python main.py                   # Dashboard de monitoramento CVM
    python main.py funds             # Tabela comparativa (apenas ativos)
    python main.py funds --all       # Inclui todas situações exceto cancelados
    python main.py funds --canceled  # Inclui todos (inclusive cancelados)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def main():
    args = sys.argv[1:]

    if args and args[0] == 'funds':
        from src.analisador_fundos import main as fundos_main
        modo = 'ativos'
        if '--canceled' in args:
            modo = 'cancelados'
        elif '--all' in args:
            modo = 'todos'
        fundos_main(modo=modo)
    elif args and args[0] in ['--help', '-h']:
        print(__doc__)
    else:
        from src.dashboard_cvm import main_dashboard
        main_dashboard()


if __name__ == "__main__":
    main()
