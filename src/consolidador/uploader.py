"""
Google Drive Uploader - Uploads consolidated CSV files to Google Drive using OAuth2.

Authentication flow:
1. First time: Run `python main.py auth` to authenticate and generate token.json
2. Subsequent runs: Uses saved token (auto-refreshes when needed)

For GitHub Actions: Store token.json contents as GOOGLE_TOKEN_JSON secret.
"""
import json
import os
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

from .config import OUTPUT_DIR


# OAuth2 scope - full Drive access to upload to any folder
SCOPES = ['https://www.googleapis.com/auth/drive']

# Token file location
PROJECT_ROOT = Path(__file__).parent.parent.parent
TOKEN_FILE = PROJECT_ROOT / 'token.json'


def find_client_secrets() -> Optional[Path]:
    """Find OAuth2 client secrets file in project root."""
    for f in PROJECT_ROOT.glob('client_secret*.json'):
        return f
    return None


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth2 callback."""

    def do_GET(self):
        """Handle the OAuth callback GET request."""
        # Parse the authorization code from the URL
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if 'code' in params:
            self.server.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'''
                <html><body style="font-family: Arial; text-align: center; padding-top: 50px;">
                <h1>Autenticado com sucesso!</h1>
                <p>Pode fechar esta janela e voltar ao terminal.</p>
                </body></html>
            ''')
        else:
            self.server.auth_code = None
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress HTTP server logs."""
        pass


def authenticate_interactive() -> Credentials:
    """
    Run interactive OAuth2 flow (opens browser).

    This only needs to be done once - generates token.json for future use.
    """
    client_secrets = find_client_secrets()
    if not client_secrets:
        raise FileNotFoundError(
            "OAuth2 client secrets not found. Download from Google Cloud Console "
            "and place client_secret_*.json in project root."
        )

    print(f"Usando credenciais: {client_secrets.name}")

    # Create flow for web application
    flow = Flow.from_client_secrets_file(
        str(client_secrets),
        scopes=SCOPES,
        redirect_uri='http://localhost:8080/'
    )

    # Generate authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )

    print("\nIniciando servidor local na porta 8080...")
    print("Abrindo navegador para autenticação...\n")

    # Start local server to receive callback
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server.auth_code = None

    # Open browser
    webbrowser.open(auth_url)

    print("Aguardando autenticação no navegador...")

    # Wait for the callback
    server.handle_request()

    if not server.auth_code:
        raise RuntimeError("Falha na autenticação - código não recebido")

    # Exchange code for credentials
    flow.fetch_token(code=server.auth_code)
    credentials = flow.credentials

    # Save token for future use
    with open(TOKEN_FILE, 'w') as f:
        f.write(credentials.to_json())

    print(f"\n✓ Token salvo em: {TOKEN_FILE}")
    print("\nPara usar no GitHub Actions, adicione o conteúdo do token.json")
    print("como secret GOOGLE_TOKEN_JSON no seu repositório.")

    return credentials


def get_credentials() -> Credentials:
    """
    Get valid credentials, refreshing if necessary.

    Priority:
    1. GOOGLE_TOKEN_JSON env var (for GitHub Actions)
    2. token.json file (for local use)
    """
    credentials = None

    # Try environment variable first (GitHub Actions)
    token_json = os.environ.get('GOOGLE_TOKEN_JSON')
    if token_json:
        try:
            token_data = json.loads(token_json)
            credentials = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            print(f"⚠ Erro ao carregar token do ambiente: {e}")

    # Try token file
    if not credentials and TOKEN_FILE.exists():
        try:
            credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            print(f"⚠ Erro ao carregar token do arquivo: {e}")

    # Refresh if expired
    if credentials and credentials.expired and credentials.refresh_token:
        print("Renovando token...")
        credentials.refresh(Request())
        # Save refreshed token
        with open(TOKEN_FILE, 'w') as f:
            f.write(credentials.to_json())

    if not credentials or not credentials.valid:
        raise RuntimeError(
            "Token não encontrado ou inválido.\n"
            "Execute 'python main.py auth' para autenticar."
        )

    return credentials


def find_file_in_folder(service, folder_id: str, filename: str) -> Optional[str]:
    """Find a file by name in a specific folder. Returns file ID or None."""
    query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()

    files = results.get('files', [])
    return files[0]['id'] if files else None


def upload_file(service, file_path: Path, folder_id: str) -> str:
    """
    Upload a file to Google Drive, replacing if exists.

    Returns the file ID.
    """
    filename = file_path.name
    mime_type = 'text/csv'

    # Check if file already exists
    existing_id = find_file_in_folder(service, folder_id, filename)

    media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=False)

    if existing_id:
        # Update existing file
        file = service.files().update(
            fileId=existing_id,
            media_body=media
        ).execute()
        print(f"  ✓ Atualizado: {filename}")
    else:
        # Create new file
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print(f"  ✓ Criado: {filename}")

    return file.get('id')


def upload_to_drive(folder_id: str) -> bool:
    """
    Upload fundos.csv and composicao_carteira.csv to Google Drive.

    Args:
        folder_id: Google Drive folder ID

    Returns:
        True if successful, False otherwise
    """
    print("\n" + "=" * 50)
    print("UPLOAD PARA GOOGLE DRIVE")
    print("=" * 50)

    # Files to upload
    files_to_upload = [
        OUTPUT_DIR / 'fundos.csv',
        OUTPUT_DIR / 'composicao_carteira.csv'
    ]

    # Check files exist
    missing = [f for f in files_to_upload if not f.exists()]
    if missing:
        print(f"\n✗ Arquivos não encontrados: {[f.name for f in missing]}")
        print("  Execute 'python main.py consolidate' primeiro.")
        return False

    try:
        # Get credentials and build service
        print("\nAutenticando...")
        credentials = get_credentials()
        service = build('drive', 'v3', credentials=credentials)

        # Upload files
        print(f"\nEnviando para pasta {folder_id}...")
        for file_path in files_to_upload:
            upload_file(service, file_path, folder_id)

        print("\n✓ Upload concluído com sucesso!")
        return True

    except Exception as e:
        print(f"\n✗ Erro no upload: {e}")
        return False
