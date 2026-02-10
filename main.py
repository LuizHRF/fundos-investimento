#!/usr/bin/env python3
"""
CVM Fundos de Investimento - Consolidador RCVM175

Consolida dados de fundos de investimento brasileiros usando o novo
sistema de registro da Resolução CVM 175 (2023).

Uso:
    python main.py                      # Consolida dados (padrão)
    python main.py consolidate          # Mesmo que acima
    python main.py consolidate --force  # Força re-download
    python main.py auth                 # Autenticar com Google (uma vez)
    python main.py refresh              # Renovar token expirado
    python main.py upload               # Upload para Google Drive
"""
import os
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

    elif args[0] == 'auth':
        from src.consolidador.uploader import authenticate_interactive

        print("=" * 50)
        print("AUTENTICAÇÃO GOOGLE DRIVE")
        print("=" * 50)
        authenticate_interactive()

    elif args[0] == 'refresh':
        from src.consolidador.uploader import refresh_token

        success = refresh_token()
        sys.exit(0 if success else 1)

    elif args[0] == 'upload':
        from src.consolidador.uploader import upload_to_drive

        # Get folder ID from env var or argument
        folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        if not folder_id and len(args) > 1:
            folder_id = args[1]

        if not folder_id:
            print("Erro: GOOGLE_DRIVE_FOLDER_ID não definido.")
            print("Use: python main.py upload <FOLDER_ID>")
            print("Ou defina a variável de ambiente GOOGLE_DRIVE_FOLDER_ID")
            sys.exit(1)

        success = upload_to_drive(folder_id)
        sys.exit(0 if success else 1)

    elif args[0] in ['--help', '-h']:
        print(__doc__)

    else:
        print(f"Comando desconhecido: {args[0]}")
        print("Use --help para ver os comandos disponíveis.")
        sys.exit(1)


if __name__ == "__main__":
    main()
