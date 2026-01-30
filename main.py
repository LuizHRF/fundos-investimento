#!/usr/bin/env python3
"""
CVM Fundos de Investimento - Consolidador RCVM175

Consolida dados de fundos de investimento brasileiros usando o novo
sistema de registro da Resolução CVM 175 (2023).

Uso:
    python main.py                   # Consolida dados (padrão)
    python main.py consolidate       # Mesmo que acima
    python main.py consolidate --force  # Força re-download
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def main():
    args = sys.argv[1:]

    # Default command is consolidate
    if not args or args[0] == 'consolidate':
        from src.consolidador import consolidate
        force = '--force' in args

        consolidate(force=force)

    elif args[0] in ['--help', '-h']:
        print(__doc__)

    else:
        print(f"Comando desconhecido: {args[0]}")
        print("Use --help para ver os comandos disponíveis.")
        sys.exit(1)


if __name__ == "__main__":
    main()
