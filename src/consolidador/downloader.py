"""
Download utilities for CVM data files with caching and ZIP extraction.
"""
import requests
import zipfile
import io
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List

from .config import CACHE_DIR, CSV_ENCODING, CSV_DELIMITER


def ensure_cache_dir() -> Path:
    """Ensure cache directory exists and return its path."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def get_cache_path(url: str) -> Path:
    """Generate cache file path from URL."""
    filename = url.split('/')[-1]
    return CACHE_DIR / filename


def url_exists(url: str, timeout: int = 10) -> bool:
    """Check if URL exists using HEAD request."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def download_csv(url: str, use_cache: bool = True, force: bool = False) -> Optional[Path]:
    """
    Download CSV file from URL with optional caching.

    Args:
        url: URL to download from
        use_cache: Whether to use cached file if available
        force: Force re-download even if cached

    Returns:
        Path to downloaded/cached file, or None if download failed
    """
    ensure_cache_dir()
    cache_path = get_cache_path(url)

    if use_cache and not force and cache_path.exists():
        print(f"  ✓ Usando cache: {cache_path.name}")
        return cache_path

    print(f"  ↓ Baixando: {url.split('/')[-1]}")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        cache_path.write_bytes(response.content)
        return cache_path

    except requests.RequestException as e:
        print(f"  ✗ Erro ao baixar {url}: {e}")
        return None


def download_zip(url: str, extract_to: Optional[Path] = None,
                 use_cache: bool = True, force: bool = False) -> Optional[Path]:
    """
    Download and extract ZIP file.

    Args:
        url: URL to download from
        extract_to: Directory to extract to (default: cache/zip_name/)
        use_cache: Whether to use cached extraction if available
        force: Force re-download and re-extract

    Returns:
        Path to extraction directory, or None if failed
    """
    ensure_cache_dir()

    zip_name = url.split('/')[-1].replace('.zip', '')
    if extract_to is None:
        extract_to = CACHE_DIR / zip_name

    # Check if already extracted
    if use_cache and not force and extract_to.exists() and any(extract_to.iterdir()):
        print(f"  ✓ Usando cache: {zip_name}/")
        return extract_to

    print(f"  ↓ Baixando: {url.split('/')[-1]}")
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()

        # Extract ZIP
        extract_to.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            zf.extractall(extract_to)

        csv_count = len(list(extract_to.glob('*.csv')))
        print(f"  ✓ Extraído: {csv_count} arquivo(s) CSV")
        return extract_to

    except requests.RequestException as e:
        print(f"  ✗ Erro ao baixar {url}: {e}")
        return None
    except zipfile.BadZipFile as e:
        print(f"  ✗ ZIP inválido {url}: {e}")
        return None


def get_monthly_urls(template: str, months: int = 6) -> List[str]:
    """
    Generate list of monthly URLs going back N months from current date.

    Args:
        template: URL template with {yyyymm} placeholder
        months: Number of months to go back

    Returns:
        List of URLs for each month
    """
    urls = []
    today = datetime.now()

    for i in range(months):
        # Go back i months
        target_date = today - timedelta(days=30 * i)
        yyyymm = target_date.strftime('%Y%m')
        url = template.format(yyyymm=yyyymm)
        urls.append(url)

    return urls


def get_available_monthly_urls(template: str, months: int = 6) -> List[str]:
    """
    Generate list of monthly URLs that actually exist on the server.

    Args:
        template: URL template with {yyyymm} placeholder
        months: Number of months to go back

    Returns:
        List of available URLs
    """
    all_urls = get_monthly_urls(template, months)
    available = []

    for url in all_urls:
        if url_exists(url):
            available.append(url)
        else:
            yyyymm = url.split('_')[-1].replace('.zip', '')
            print(f"  ⚠ Não disponível: {yyyymm}")

    return available
