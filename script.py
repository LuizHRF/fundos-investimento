from ckanapi import RemoteCKAN
import json
from typing import List, Dict, Optional
from datetime import datetime
import sys
import os
import time


# ====================
# COLOR & UTILITY HELPERS
# ====================

class Colors:
    """ANSI color codes for terminal output"""
    # Basic colors
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright foreground colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_CYAN = '\033[96m'

    @staticmethod
    def is_tty():
        """Check if output is to a terminal (supports colors)"""
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

    @staticmethod
    def enable_windows_colors():
        """Enable ANSI colors on Windows 10+"""
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # Enable ANSI/VT100 escape sequences
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except Exception:
                pass  # Fail silently if colors can't be enabled

    @staticmethod
    def colorize(text: str, color: str, bold: bool = False, disable_colors: bool = False) -> str:
        """Apply color to text if terminal supports it"""
        if disable_colors or not Colors.is_tty():
            return text

        prefix = Colors.BOLD if bold else ''
        return f"{prefix}{color}{text}{Colors.RESET}"


def format_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp to human-readable format"""
    if not timestamp_str:
        return "N/A"

    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return timestamp_str


def time_since(timestamp_str: str) -> str:
    """Calculate human-readable time since timestamp"""
    if not timestamp_str:
        return "N/A"

    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        # Make datetime offset-aware if it's naive
        if dt.tzinfo is None:
            from datetime import timezone
            dt = dt.replace(tzinfo=timezone.utc)

        now = datetime.now(dt.tzinfo)
        delta = now - dt

        days = delta.days
        hours = delta.seconds // 3600

        if days > 365:
            years = days // 365
            return f"{years}y ago"
        elif days > 30:
            months = days // 30
            return f"{months}mo ago"
        elif days > 0:
            return f"{days}d ago"
        elif hours > 0:
            return f"{hours}h ago"
        else:
            minutes = delta.seconds // 60
            return f"{minutes}m ago"
    except Exception:
        return "N/A"


def get_time_color(timestamp_str: str) -> str:
    """Get color based on how recent the timestamp is"""
    if not timestamp_str:
        return Colors.WHITE

    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        # Make datetime offset-aware if it's naive
        if dt.tzinfo is None:
            from datetime import timezone
            dt = dt.replace(tzinfo=timezone.utc)

        now = datetime.now(dt.tzinfo)
        delta = now - dt
        days = delta.days

        if days < 7:
            return Colors.GREEN
        elif days < 30:
            return Colors.YELLOW
        else:
            return Colors.RED
    except Exception:
        return Colors.WHITE


def get_fund_type_from_id(dataset_id: str) -> str:
    """Extract fund type from dataset ID"""
    if not dataset_id:
        return "OTHER"

    dataset_lower = dataset_id.lower()

    # Check for specific fund types
    if dataset_lower.startswith('fi-') and not dataset_lower.startswith(('fii-', 'fip-', 'fie-', 'fidc-', 'fiagro-')):
        return "FI"
    elif dataset_lower.startswith('fii-'):
        return "FII"
    elif dataset_lower.startswith('fip-'):
        return "FIP"
    elif dataset_lower.startswith('fidc-'):
        return "FIDC"
    elif dataset_lower.startswith('fiagro-'):
        return "FIAGRO"
    elif dataset_lower.startswith('fie-'):
        return "FIE"
    else:
        return "OTHER"


def create_bar_chart(value: int, total: int, max_width: int = 40) -> str:
    """Create a simple ASCII bar chart"""
    if total == 0:
        return ""

    percentage = value / total
    filled = int(percentage * max_width)
    bar = "█" * filled

    return bar


class CVMDataExtractor:
    """Extrator de dados do Portal de Dados Abertos da CVM usando ckanapi"""
    
    def __init__(self, state_file: str = 'cvm_state.json', enable_colors: bool = True, api_throttle: float = 0.5, output_file: Optional[str] = None):
        # Inicializar conexão com o portal CKAN da CVM
        self.ckan = RemoteCKAN('https://dados.cvm.gov.br')
        self.group_id = 'fundos-de-investimento'
        self.state_file = state_file
        self.enable_colors = enable_colors and Colors.is_tty()
        self.api_throttle = api_throttle
        self.output_file = output_file
        self._output_buffer = []  # Buffer for collecting output

        # Enable Windows color support
        if enable_colors:
            Colors.enable_windows_colors()

    def _print(self, text: str = "", to_file_only: bool = False):
        """Print to console and optionally buffer for file output"""
        # Strip ANSI codes for file output
        if self.output_file:
            # Remove ANSI escape sequences for plain text file
            import re
            clean_text = re.sub(r'\033\[[0-9;]*m', '', text)
            self._output_buffer.append(clean_text)

        # Print to console unless file-only
        if not to_file_only:
            print(text)

    def _save_output_to_file(self):
        """Save buffered output to text file"""
        if self.output_file and self._output_buffer:
            try:
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self._output_buffer))
                print(Colors.colorize(f"\n✅ Dashboard salvo em: {self.output_file}", Colors.GREEN))
            except Exception as e:
                print(f"Warning: Could not save output file: {e}")

    def _clear_output_buffer(self):
        """Clear the output buffer"""
        self._output_buffer = []

    def get_group_info(self) -> Dict:
        """Obtém informações sobre o grupo de Fundos de Investimento"""
        try:
            group_info = self.ckan.action.group_package_show(
                id=self.group_id,
                limit=1000
            )
            return group_info
        except Exception as e:
            print(f"❌ Erro ao obter informações do grupo: {e}")
            raise
    
    def list_all_datasets(self) -> List[Dict]:
        """Lista todos os datasets do grupo de Fundos de Investimento"""
        datasets = self.get_group_info()

        print(f"✅ Encontrados {len(datasets)} conjuntos de dados no grupo '{self.group_id}'\n")
        return datasets
    
    def get_dataset_details(self, dataset_id: str) -> Dict:
        """Obtém detalhes completos de um dataset específico"""
        try:
            dataset = self.ckan.action.package_show(id=dataset_id)
            return dataset
        except Exception as e:
            print(f"❌ Erro ao obter detalhes do dataset {dataset_id}: {e}")
            raise
    
    def search_datasets(self, query: str, rows: int = 100) -> List[Dict]:
        """Busca datasets por palavra-chave"""
        try:
            results = self.ckan.action.package_search(
                q=query,
                rows=rows,
                fq=f'groups:{self.group_id}'
            )
            return results['results']
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            raise
    
    def extract_all_resources(self, verbose: bool = True) -> Dict[str, Dict]:
        """
        Extrai todos os recursos (arquivos) de todos os datasets
        Retorna um dicionário estruturado com informações completas
        """
        datasets = self.list_all_datasets()
        all_data = {}
        
        for idx, dataset in enumerate(datasets, 1):
            dataset_id = dataset['name']
            dataset_title = dataset['title']
            
            if verbose:
                print(f"[{idx}/{len(datasets)}] Processando: {dataset_title}")
            
            # Obter detalhes completos do dataset
            details = self.get_dataset_details(dataset_id)
            
            # Estruturar informações
            all_data[dataset_id] = {
                'title': details.get('title', ''),
                'name': dataset_id,
                'notes': details.get('notes', ''),  # Descrição
                'url': f"https://dados.cvm.gov.br/dataset/{dataset_id}",
                'organization': details.get('organization', {}).get('title', ''),
                'metadata_created': details.get('metadata_created', ''),
                'metadata_modified': details.get('metadata_modified', ''),
                'tags': [tag['name'] for tag in details.get('tags', [])],
                'groups': [group['name'] for group in details.get('groups', [])],
                'num_resources': details.get('num_resources', 0),
                'resources': []
            }
            
            # Extrair recursos
            for resource in details.get('resources', []):
                resource_info = {
                    'id': resource.get('id', ''),
                    'name': resource.get('name', 'Sem nome'),
                    'description': resource.get('description', ''),
                    'format': resource.get('format', 'N/A'),
                    'url': resource.get('url', ''),
                    'size': resource.get('size'),
                    'created': resource.get('created', ''),
                    'last_modified': resource.get('last_modified', ''),
                    'mimetype': resource.get('mimetype', '')
                }
                all_data[dataset_id]['resources'].append(resource_info)
            
            if verbose:
                print(f"   └─ {len(details.get('resources', []))} recursos encontrados\n")
        
        return all_data

    def extract_all_resources_smart(self, previous_state: Optional[Dict] = None, verbose: bool = True) -> Dict[str, Dict]:
        """
        Smart extraction that only fetches details for changed datasets.
        Falls back to full extraction if no previous state.
        """
        if not previous_state or 'datasets' not in previous_state:
            if verbose:
                print("No previous state found. Performing full extraction...")
            return self.extract_all_resources(verbose=verbose)

        datasets = self.list_all_datasets()
        all_data = {}
        fetch_count = 0
        cached_count = 0
        prev_datasets = previous_state.get('datasets', {})

        for idx, dataset in enumerate(datasets, 1):
            dataset_id = dataset['name']
            dataset_title = dataset['title']

            # Check if dataset metadata changed
            current_metadata_modified = dataset.get('metadata_modified')
            prev_dataset = prev_datasets.get(dataset_id)

            if (prev_dataset and
                prev_dataset.get('metadata_modified') == current_metadata_modified):
                # Use cached data - reconstruct from state
                if verbose:
                    print(f"[{idx}/{len(datasets)}] {dataset_title} (cached)")

                all_data[dataset_id] = self._reconstruct_from_state(dataset, prev_dataset)
                cached_count += 1
            else:
                # Fetch fresh data
                if verbose:
                    print(f"[{idx}/{len(datasets)}] Fetching: {dataset_title}")

                # API throttling
                if self.api_throttle > 0 and fetch_count > 0:
                    time.sleep(self.api_throttle)

                details = self.get_dataset_details(dataset_id)

                # Structure dataset info
                all_data[dataset_id] = {
                    'title': details.get('title', ''),
                    'name': dataset_id,
                    'notes': details.get('notes', ''),
                    'url': f"https://dados.cvm.gov.br/dataset/{dataset_id}",
                    'organization': details.get('organization', {}).get('title', ''),
                    'metadata_created': details.get('metadata_created', ''),
                    'metadata_modified': details.get('metadata_modified', ''),
                    'tags': [tag['name'] for tag in details.get('tags', [])],
                    'groups': [group['name'] for group in details.get('groups', [])],
                    'num_resources': details.get('num_resources', 0),
                    'resources': []
                }

                # Extract resources
                for resource in details.get('resources', []):
                    resource_info = {
                        'id': resource.get('id', ''),
                        'name': resource.get('name', 'Sem nome'),
                        'description': resource.get('description', ''),
                        'format': resource.get('format', 'N/A'),
                        'url': resource.get('url', ''),
                        'size': resource.get('size'),
                        'created': resource.get('created', ''),
                        'last_modified': resource.get('last_modified', ''),
                        'mimetype': resource.get('mimetype', '')
                    }
                    all_data[dataset_id]['resources'].append(resource_info)

                fetch_count += 1

                if verbose:
                    print(f"   └─ {len(details.get('resources', []))} recursos encontrados\n")

        if verbose:
            print(Colors.colorize(f"\n✓ Fetched: {fetch_count} datasets | Cached: {cached_count} datasets", Colors.GREEN, bold=True))

        return all_data

    def _reconstruct_from_state(self, dataset_summary: Dict, prev_dataset: Dict) -> Dict:
        """Reconstruct dataset info from cached state"""
        dataset_id = dataset_summary['name']

        # Rebuild resource list from state
        resources = []
        for resource_id, resource_data in prev_dataset.get('resources', {}).items():
            resources.append({
                'id': resource_id,
                'name': resource_data.get('name', ''),
                'description': '',
                'format': resource_data.get('format', ''),
                'url': '',  # Not stored in state, not needed for display
                'size': resource_data.get('size'),
                'created': '',
                'last_modified': resource_data.get('last_modified', ''),
                'mimetype': ''
            })

        return {
            'title': dataset_summary.get('title', ''),
            'name': dataset_id,
            'notes': '',
            'url': f"https://dados.cvm.gov.br/dataset/{dataset_id}",
            'organization': 'CVM',
            'metadata_created': '',
            'metadata_modified': prev_dataset.get('metadata_modified', ''),
            'tags': [],
            'groups': [],
            'num_resources': prev_dataset.get('num_resources', 0),
            'resources': resources
        }

    def get_latest_resources(self, format_filter: str = None) -> List[Dict]:
        """
        Obtém os recursos mais recentes, opcionalmente filtrados por formato

        Args:
            format_filter: Filtrar por formato (ex: 'CSV', 'ZIP', 'TXT')
        """
        all_data = self.extract_all_resources(verbose=False)
        latest_resources = []

        for dataset_id, dataset_info in all_data.items():
            for resource in dataset_info['resources']:
                if format_filter is None or resource['format'].upper() == format_filter.upper():
                    latest_resources.append({
                        'dataset': dataset_info['title'],
                        'dataset_id': dataset_id,
                        'resource_name': resource['name'],
                        'format': resource['format'],
                        'url': resource['url'],
                        'last_modified': resource['last_modified']
                    })

        # Ordenar por data de modificação (mais recente primeiro)
        latest_resources.sort(
            key=lambda x: x['last_modified'] if x['last_modified'] else '',
            reverse=True
        )

        return latest_resources

    def load_state(self, filename: Optional[str] = None) -> Dict:
        """Load previous run state from JSON file"""
        if filename is None:
            filename = self.state_file

        if not os.path.exists(filename):
            return {}

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                state = json.load(f)
            return state
        except Exception as e:
            print(f"Warning: Could not load state file {filename}: {e}")
            print("Proceeding without previous state...")
            return {}

    def save_state(self, all_data: Dict, filename: Optional[str] = None):
        """Save current state to JSON file"""
        if filename is None:
            filename = self.state_file

        # Calculate summary statistics
        total_resources = sum(len(dataset['resources']) for dataset in all_data.values())
        format_count = {}
        for dataset in all_data.values():
            for resource in dataset['resources']:
                fmt = resource['format']
                format_count[fmt] = format_count.get(fmt, 0) + 1

        # Build state structure
        state = {
            'last_run_timestamp': datetime.now().isoformat(),
            'datasets': {},
            'summary': {
                'total_datasets': len(all_data),
                'total_resources': total_resources,
                'format_distribution': format_count
            }
        }

        # Store dataset metadata and resources
        for dataset_id, dataset_info in all_data.items():
            state['datasets'][dataset_id] = {
                'metadata_modified': dataset_info.get('metadata_modified', ''),
                'num_resources': dataset_info.get('num_resources', 0),
                'resources': {}
            }

            # Store resource metadata
            for resource in dataset_info.get('resources', []):
                state['datasets'][dataset_id]['resources'][resource['id']] = {
                    'last_modified': resource.get('last_modified', ''),
                    'name': resource.get('name', ''),
                    'format': resource.get('format', ''),
                    'size': resource.get('size')
                }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            print(Colors.colorize(f"Estado salvo em: {filename}", Colors.GREEN))
        except Exception as e:
            print(f"Warning: Could not save state file {filename}: {e}")

    def detect_changes(self, current_data: Dict, previous_state: Dict) -> Dict:
        """Detect changes between current data and previous state"""
        changes = {
            'new_datasets': [],
            'modified_datasets': [],
            'deleted_datasets': [],
            'new_resources': [],
            'modified_resources': [],
            'deleted_resources': []
        }

        # If no previous state, everything is new
        if not previous_state or 'datasets' not in previous_state:
            for dataset_id, dataset_info in current_data.items():
                changes['new_datasets'].append({
                    'id': dataset_id,
                    'title': dataset_info['title'],
                    'num_resources': len(dataset_info['resources'])
                })
            return changes

        prev_datasets = previous_state.get('datasets', {})

        # Check for new and modified datasets
        for dataset_id, current_info in current_data.items():
            if dataset_id not in prev_datasets:
                changes['new_datasets'].append({
                    'id': dataset_id,
                    'title': current_info['title'],
                    'num_resources': len(current_info['resources'])
                })
            else:
                prev_dataset = prev_datasets[dataset_id]

                # Compare metadata_modified timestamps
                if current_info.get('metadata_modified') != prev_dataset.get('metadata_modified'):
                    changes['modified_datasets'].append({
                        'id': dataset_id,
                        'title': current_info['title'],
                        'old_modified': prev_dataset.get('metadata_modified'),
                        'new_modified': current_info.get('metadata_modified')
                    })

                # Check resources
                current_resource_ids = {r['id'] for r in current_info['resources']}
                prev_resource_ids = set(prev_dataset.get('resources', {}).keys())

                # New resources
                for resource in current_info['resources']:
                    if resource['id'] not in prev_resource_ids:
                        changes['new_resources'].append({
                            'dataset_id': dataset_id,
                            'dataset_title': current_info['title'],
                            'resource': resource
                        })
                    else:
                        # Modified resources (check last_modified timestamp)
                        prev_resource = prev_dataset['resources'].get(resource['id'], {})
                        if resource.get('last_modified') != prev_resource.get('last_modified'):
                            changes['modified_resources'].append({
                                'dataset_id': dataset_id,
                                'dataset_title': current_info['title'],
                                'resource': resource,
                                'old_modified': prev_resource.get('last_modified'),
                                'new_modified': resource.get('last_modified')
                            })

                # Deleted resources
                for resource_id in prev_resource_ids - current_resource_ids:
                    changes['deleted_resources'].append({
                        'dataset_id': dataset_id,
                        'resource_id': resource_id,
                        'resource_name': prev_dataset['resources'][resource_id].get('name', 'Unknown')
                    })

        # Check for deleted datasets
        for dataset_id in prev_datasets.keys():
            if dataset_id not in current_data:
                prev_dataset = prev_datasets[dataset_id]
                changes['deleted_datasets'].append({
                    'id': dataset_id,
                    'num_resources': prev_dataset.get('num_resources', 0)
                })

        return changes

    def classify_by_fund_type(self, all_data: Dict) -> Dict:
        """Group datasets by fund type"""
        fund_types = {}

        for dataset_id, dataset_info in all_data.items():
            fund_type = get_fund_type_from_id(dataset_id)

            if fund_type not in fund_types:
                fund_types[fund_type] = {
                    'datasets': [],
                    'total_resources': 0,
                    'latest_update': None
                }

            # Add dataset to fund type group
            fund_types[fund_type]['datasets'].append({
                'id': dataset_id,
                'info': dataset_info
            })

            # Count resources
            fund_types[fund_type]['total_resources'] += len(dataset_info.get('resources', []))

            # Track latest update
            current_modified = dataset_info.get('metadata_modified', '')
            if current_modified:
                if not fund_types[fund_type]['latest_update'] or current_modified > fund_types[fund_type]['latest_update']:
                    fund_types[fund_type]['latest_update'] = current_modified

        return fund_types

    def infer_update_frequency(self, dataset_id: str, dataset_info: Dict) -> str:
        """Infer update frequency from dataset ID and metadata"""
        id_lower = dataset_id.lower()

        # Check dataset ID for frequency indicators
        if 'diario' in id_lower or 'inf_diario' in id_lower:
            return 'DIÁRIO'
        elif 'mensal' in id_lower or 'inf_mensal' in id_lower:
            return 'MENSAL'
        elif 'trimestral' in id_lower or 'inf_trimestral' in id_lower:
            return 'TRIMESTRAL'
        elif 'quadrimestral' in id_lower or 'inf_quadrimestral' in id_lower:
            return 'QUADRIMESTRAL'
        elif 'anual' in id_lower or 'inf_anual' in id_lower:
            return 'ANUAL'

        # Analyze resource patterns
        resource_names = [r['name'].lower() for r in dataset_info.get('resources', [])]

        # Count monthly patterns
        monthly_keywords = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                           'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
        monthly_count = sum(1 for name in resource_names
                          if any(month in name for month in monthly_keywords))

        if monthly_count >= 6:
            return 'MENSAL'

        # Check notes for frequency information
        notes = dataset_info.get('notes', '').lower()
        if 'diariamente' in notes or 'dia' in notes or 'daily' in notes:
            return 'DIÁRIO'
        elif 'mensal' in notes or 'mês' in notes or 'monthly' in notes:
            return 'MENSAL'

        return 'VARIÁVEL'

    def print_dashboard(self, all_data: Dict[str, Dict], changes: Optional[Dict] = None, previous_state: Optional[Dict] = None, save_to_file: bool = None):
        """Print enhanced dashboard with fund type breakdown and statistics"""
        # Determine if we should save to file
        if save_to_file is None:
            save_to_file = self.output_file is not None

        # Clear buffer if saving to file
        if save_to_file:
            self._clear_output_buffer()
        # Calculate statistics
        total_datasets = len(all_data)
        total_resources = sum(len(dataset['resources']) for dataset in all_data.values())

        # Format distribution
        format_count = {}
        for dataset in all_data.values():
            for resource in dataset['resources']:
                fmt = resource['format']
                format_count[fmt] = format_count.get(fmt, 0) + 1

        # Classify by fund type
        fund_types = self.classify_by_fund_type(all_data)

        # Print header
        self._print("\n" + "=" * 100)
        header_text = "CVM FUNDOS DE INVESTIMENTO - DASHBOARD"
        self._print(Colors.colorize(header_text.center(100), Colors.CYAN, bold=True))
        self._print("=" * 100)

        # Timestamp info
        current_time = format_timestamp(datetime.now().isoformat())
        previous_time = ""
        if previous_state and 'last_run_timestamp' in previous_state:
            previous_time = f" | Anterior: {format_timestamp(previous_state['last_run_timestamp'])}"

        self._print(f"Última Atualização: {current_time}{previous_time}")
        self._print("-" * 100)

        # Summary statistics
        self._print("\n" + Colors.colorize("ESTATÍSTICAS GERAIS", Colors.CYAN, bold=True))
        self._print(f"  Total de Datasets: {Colors.colorize(str(total_datasets), Colors.WHITE, bold=True)} | " +
              f"Total de Recursos: {Colors.colorize(str(total_resources), Colors.WHITE, bold=True)} | " +
              f"Tipos de Fundos: {Colors.colorize(str(len(fund_types)), Colors.WHITE, bold=True)}")

        # Format distribution
        self._print("\n" + Colors.colorize("DISTRIBUIÇÃO POR FORMATO", Colors.CYAN, bold=True))
        sorted_formats = sorted(format_count.items(), key=lambda x: x[1], reverse=True)
        for fmt, count in sorted_formats:
            percentage = (count / total_resources * 100) if total_resources > 0 else 0
            bar = create_bar_chart(count, total_resources, max_width=35)
            self._print(f"  {fmt:>4}: {count:>3} ({percentage:>5.1f}%) {Colors.colorize(bar, Colors.BLUE)}")

        # Fund type breakdown
        self._print("\n" + "=" * 100)
        self._print(Colors.colorize("DETALHAMENTO POR TIPO DE FUNDO", Colors.CYAN, bold=True))
        self._print("=" * 100 + "\n")

        # Fund type labels
        fund_type_labels = {
            'FI': 'FUNDOS DE INVESTIMENTO',
            'FII': 'FUNDOS DE INVESTIMENTO IMOBILIÁRIO',
            'FIP': 'FUNDOS DE INVESTIMENTO EM PARTICIPAÇÕES',
            'FIDC': 'FUNDOS DE INVESTIMENTO EM DIREITOS CREDITÓRIOS',
            'FIAGRO': 'FUNDOS DE INVESTIMENTO NAS CADEIAS AGROINDUSTRIAIS',
            'FIE': 'FUNDOS DE INVESTIMENTO ESTRUTURADOS',
            'OTHER': 'OUTROS'
        }

        # Sort fund types by number of datasets (descending)
        sorted_fund_types = sorted(fund_types.items(),
                                   key=lambda x: len(x[1]['datasets']),
                                   reverse=True)

        for fund_type, type_data in sorted_fund_types:
            label = fund_type_labels.get(fund_type, fund_type)
            num_datasets = len(type_data['datasets'])
            num_resources = type_data['total_resources']

            # Print fund type header
            header = f"[{fund_type}] {label}"
            stats = f"{num_datasets} datasets | {num_resources} recursos"
            self._print(Colors.colorize(header, Colors.YELLOW, bold=True).ljust(70) + stats)
            self._print("-" * 100)

            # Latest update for this fund type
            if type_data['latest_update']:
                time_ago = time_since(type_data['latest_update'])
                time_color = get_time_color(type_data['latest_update'])
                self._print(f"  Última Atualização: {format_timestamp(type_data['latest_update'])} " +
                      f"({Colors.colorize(time_ago, time_color)})")
                self._print()

            # List datasets in this fund type
            # Sort datasets by metadata_modified (most recent first)
            sorted_datasets = sorted(type_data['datasets'],
                                    key=lambda x: x['info'].get('metadata_modified', ''),
                                    reverse=True)

            for dataset_entry in sorted_datasets[:10]:  # Show top 10
                dataset_id = dataset_entry['id']
                dataset_info = dataset_entry['info']
                frequency = self.infer_update_frequency(dataset_id, dataset_info)
                num_res = len(dataset_info.get('resources', []))
                last_mod = dataset_info.get('metadata_modified', '')

                # Color code frequency
                freq_color = Colors.GREEN if frequency == 'DIÁRIO' else \
                            Colors.BLUE if frequency == 'MENSAL' else \
                            Colors.MAGENTA if frequency in ['TRIMESTRAL', 'QUADRIMESTRAL'] else \
                            Colors.CYAN if frequency == 'ANUAL' else \
                            Colors.WHITE

                time_ago = time_since(last_mod)
                time_color = get_time_color(last_mod)

                self._print(f"  {dataset_id:30} " +
                      f"{Colors.colorize(f'[{frequency}]', freq_color):30} " +
                      f"{num_res:>2} recursos   " +
                      f"Atualizado: {Colors.colorize(time_ago, time_color)}")

            if len(type_data['datasets']) > 10:
                remaining = len(type_data['datasets']) - 10
                self._print(f"\n  ... e mais {remaining} dataset(s)")

            self._print()

        self._print("=" * 100 + "\n")

        # Print changes if detected
        if changes:
            self.print_change_summary(changes, previous_state, save_to_file=False)

        # Save to file if requested
        if save_to_file:
            self._save_output_to_file()

    def print_change_summary(self, changes: Dict, previous_state: Optional[Dict] = None, save_to_file: bool = True):
        """Print summary of detected changes"""
        # Check if any changes detected
        has_changes = any([
            changes.get('new_datasets'),
            changes.get('modified_datasets'),
            changes.get('deleted_datasets'),
            changes.get('new_resources'),
            changes.get('modified_resources'),
            changes.get('deleted_resources')
        ])

        if not has_changes:
            self._print(Colors.colorize("Nenhuma mudança detectada desde a última execução.", Colors.GREEN, bold=True))
            self._print()
            return

        self._print("=" * 100)
        header = "MUDANÇAS DETECTADAS"
        if previous_state and 'last_run_timestamp' in previous_state:
            since = format_timestamp(previous_state['last_run_timestamp'])
            header += f" (Desde: {since})"
        self._print(Colors.colorize(header, Colors.CYAN, bold=True))
        self._print("=" * 100 + "\n")

        # New datasets
        if changes.get('new_datasets'):
            self._print(Colors.colorize(f"NOVOS DATASETS ({len(changes['new_datasets'])}): ", Colors.GREEN, bold=True))
            for ds in changes['new_datasets'][:5]:  # Show first 5
                self._print(f"  + {ds['id']}: {ds['title']} ({ds['num_resources']} recursos)")
            if len(changes['new_datasets']) > 5:
                self._print(f"  ... e mais {len(changes['new_datasets']) - 5}")
            self._print()

        # New resources
        if changes.get('new_resources'):
            self._print(Colors.colorize(f"NOVOS RECURSOS ({len(changes['new_resources'])}): ", Colors.GREEN, bold=True))
            for res_change in changes['new_resources'][:10]:  # Show first 10
                resource = res_change['resource']
                self._print(f"  + {res_change['dataset_id']}: {resource['name']} [{resource['format']}]")
            if len(changes['new_resources']) > 10:
                self._print(f"  ... e mais {len(changes['new_resources']) - 10}")
            self._print()

        # Modified datasets
        if changes.get('modified_datasets'):
            self._print(Colors.colorize(f"DATASETS MODIFICADOS ({len(changes['modified_datasets'])}): ", Colors.YELLOW, bold=True))
            for ds in changes['modified_datasets'][:5]:
                old_time = format_timestamp(ds['old_modified'])
                new_time = format_timestamp(ds['new_modified'])
                self._print(f"  ~ {ds['id']}: {ds['title']}")
                self._print(f"    {old_time} -> {new_time}")
            if len(changes['modified_datasets']) > 5:
                self._print(f"  ... e mais {len(changes['modified_datasets']) - 5}")
            self._print()

        # Modified resources
        if changes.get('modified_resources'):
            self._print(Colors.colorize(f"RECURSOS MODIFICADOS ({len(changes['modified_resources'])}): ", Colors.YELLOW, bold=True))
            for res_change in changes['modified_resources'][:10]:
                resource = res_change['resource']
                new_time = format_timestamp(res_change['new_modified'])
                self._print(f"  ~ {res_change['dataset_id']}: {resource['name']} [{resource['format']}]")
                self._print(f"    Atualizado: {new_time}")
            if len(changes['modified_resources']) > 10:
                self._print(f"  ... e mais {len(changes['modified_resources']) - 10}")
            self._print()

        # Deleted resources
        if changes.get('deleted_resources'):
            self._print(Colors.colorize(f"RECURSOS REMOVIDOS ({len(changes['deleted_resources'])}): ", Colors.RED, bold=True))
            for res in changes['deleted_resources'][:10]:
                self._print(f"  - {res['dataset_id']}: {res['resource_name']}")
            if len(changes['deleted_resources']) > 10:
                self._print(f"  ... e mais {len(changes['deleted_resources']) - 10}")
            self._print()

        # Deleted datasets
        if changes.get('deleted_datasets'):
            self._print(Colors.colorize(f"DATASETS REMOVIDOS ({len(changes['deleted_datasets'])}): ", Colors.RED, bold=True))
            for ds in changes['deleted_datasets']:
                self._print(f"  - {ds['id']} ({ds['num_resources']} recursos)")
            self._print()

        self._print("=" * 100 + "\n")

    def print_summary(self, all_data: Dict[str, Dict]):
        """Imprime um resumo detalhado de todos os dados"""
        print("\n" + "="*100)
        print("RESUMO COMPLETO DOS DADOS DE FUNDOS DE INVESTIMENTO - CVM")
        print("="*100 + "\n")
        
        total_resources = sum(len(dataset['resources']) for dataset in all_data.values())
        
        # Estatísticas por formato
        format_count = {}
        for dataset in all_data.values():
            for resource in dataset['resources']:
                fmt = resource['format']
                format_count[fmt] = format_count.get(fmt, 0) + 1
        
        print(f"📊 Estatísticas Gerais:")
        print(f"   • Total de datasets: {len(all_data)}")
        print(f"   • Total de recursos: {total_resources}")
        print(f"\n📁 Distribuição por formato:")
        for fmt, count in sorted(format_count.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {fmt}: {count} arquivo(s)")
        
        print(f"\n{'='*100}")
        print("DETALHAMENTO POR DATASET")
        print(f"{'='*100}\n")
        
        for idx, (dataset_id, dataset_info) in enumerate(all_data.items(), 1):
            print(f"{idx}. 📦 {dataset_info['title']}")
            print(f"   ID: {dataset_id}")
            print(f"   URL: {dataset_info['url']}")
            print(f"   Recursos: {dataset_info['num_resources']}")
            print(f"   Última atualização: {dataset_info['metadata_modified']}")
            
            if dataset_info['tags']:
                print(f"   Tags: {', '.join(dataset_info['tags'])}")
            
            # Mostrar primeiros 3 recursos
            for ridx, resource in enumerate(dataset_info['resources'][:3], 1):
                print(f"      {ridx}. {resource['name']} ({resource['format']})")
                if resource['size']:
                    size_mb = int(resource['size']) / (1024 * 1024)
                    print(f"         Tamanho: {size_mb:.2f} MB")
                print(f"         URL: {resource['url'][:80]}...")
            
            if len(dataset_info['resources']) > 3:
                print(f"      ... e mais {len(dataset_info['resources']) - 3} recursos")
            
            print()
        
        print(f"{'='*100}\n")
    
    # def download_resource(self, url: str, output_path: str):
    #     """Download de um recurso específico com barra de progresso"""
    #     import requests
    #     from tqdm import tqdm
        
    #     print(f"📥 Baixando: {url}")
        
    #     response = requests.get(url, stream=True)
    #     response.raise_for_status()
        
    #     total_size = int(response.headers.get('content-length', 0))
        
    #     with open(output_path, 'wb') as f, tqdm(
    #         desc=output_path,
    #         total=total_size,
    #         unit='iB',
    #         unit_scale=True,
    #         unit_divisor=1024,
    #     ) as pbar:
    #         for chunk in response.iter_content(chunk_size=8192):
    #             size = f.write(chunk)
    #             pbar.update(size)
        
    #     print(f"✅ Salvo em: {output_path}\n")
    
    def export_to_json(self, all_data: Dict, filename: str = 'cvm_fundos_completo.json'):
        """Exporta todos os dados para JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Dados exportados para: {filename}")
    
    def export_to_csv(self, all_data: Dict, filename: str = 'cvm_fundos_recursos.csv'):
        """Exporta lista de recursos para CSV"""
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Dataset', 'Dataset_ID', 'Recurso', 'Formato', 
                'URL', 'Tamanho', 'Última_Modificação'
            ])
            
            for dataset_id, dataset_info in all_data.items():
                for resource in dataset_info['resources']:
                    writer.writerow([
                        dataset_info['title'],
                        dataset_id,
                        resource['name'],
                        resource['format'],
                        resource['url'],
                        resource['size'],
                        resource['last_modified']
                    ])
        
        print(f"✅ Lista de recursos exportada para: {filename}")

    def export_metadata_summary(self, all_data: Dict, changes: Optional[Dict] = None, filename: str = 'cvm_metadata_summary.json'):
        """Export dashboard metadata summary to JSON"""
        # Calculate statistics
        total_datasets = len(all_data)
        total_resources = sum(len(dataset['resources']) for dataset in all_data.values())

        # Format distribution
        format_count = {}
        for dataset in all_data.values():
            for resource in dataset['resources']:
                fmt = resource['format']
                format_count[fmt] = format_count.get(fmt, 0) + 1

        # Classify by fund type
        fund_types = self.classify_by_fund_type(all_data)

        # Build summary structure
        summary = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_datasets': total_datasets,
                'total_resources': total_resources,
                'total_fund_types': len(fund_types)
            },
            'format_distribution': format_count,
            'fund_types': {}
        }

        # Add fund type details
        for fund_type, type_data in fund_types.items():
            summary['fund_types'][fund_type] = {
                'num_datasets': len(type_data['datasets']),
                'total_resources': type_data['total_resources'],
                'latest_update': type_data['latest_update'],
                'datasets': []
            }

            # Add dataset details
            for dataset_entry in type_data['datasets']:
                dataset_id = dataset_entry['id']
                dataset_info = dataset_entry['info']
                frequency = self.infer_update_frequency(dataset_id, dataset_info)

                summary['fund_types'][fund_type]['datasets'].append({
                    'id': dataset_id,
                    'title': dataset_info.get('title', ''),
                    'update_frequency': frequency,
                    'num_resources': len(dataset_info.get('resources', [])),
                    'metadata_modified': dataset_info.get('metadata_modified', ''),
                    'url': dataset_info.get('url', '')
                })

        # Add changes if available
        if changes:
            summary['changes'] = {
                'new_datasets': len(changes.get('new_datasets', [])),
                'modified_datasets': len(changes.get('modified_datasets', [])),
                'deleted_datasets': len(changes.get('deleted_datasets', [])),
                'new_resources': len(changes.get('new_resources', [])),
                'modified_resources': len(changes.get('modified_resources', [])),
                'deleted_resources': len(changes.get('deleted_resources', []))
            }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            print(Colors.colorize(f"✅ Metadata summary exported to: {filename}", Colors.GREEN))
        except Exception as e:
            print(f"Warning: Could not export metadata summary: {e}")


# ====================
# EXEMPLOS DE USO
# ====================

def exemplo_basico():
    """Exemplo 1: Uso básico - listar todos os datasets"""
    print("\n🔷 EXEMPLO 1: Listar todos os datasets\n")
    
    extractor = CVMDataExtractor()
    all_data = extractor.extract_all_resources()
    extractor.print_summary(all_data)

def exemplo_busca():
    """Exemplo 2: Buscar datasets específicos"""
    print("\n🔷 EXEMPLO 2: Buscar datasets de FII\n")
    
    extractor = CVMDataExtractor()
    results = extractor.search_datasets('FII')
    
    print(f"Encontrados {len(results)} datasets relacionados a FII:")
    for dataset in results:
        print(f"  • {dataset['title']}")

def exemplo_recursos_recentes():
    """Exemplo 3: Listar recursos CSV mais recentes"""
    print("\n🔷 EXEMPLO 3: Recursos CSV mais recentes\n")
    
    extractor = CVMDataExtractor()
    csv_resources = extractor.get_latest_resources(format_filter='CSV')
    
    print("Top 10 arquivos CSV mais recentes:")
    for idx, resource in enumerate(csv_resources[:10], 1):
        print(f"{idx}. {resource['resource_name']}")
        print(f"   Dataset: {resource['dataset']}")
        print(f"   Última modificação: {resource['last_modified']}")
        print(f"   URL: {resource['url'][:80]}...\n")

def exemplo_download():
    """Exemplo 4: Download de arquivo específico"""
    print("\n🔷 EXEMPLO 4: Download de arquivo\n")
    
    extractor = CVMDataExtractor()
    
    # Obter o cadastro de fundos (sempre atualizado)
    dataset = extractor.get_dataset_details('fi-cad')
    
    # Pegar o primeiro recurso CSV
    csv_resources = [r for r in dataset['resources'] if r['format'] == 'CSV']
    
    if csv_resources:
        resource = csv_resources[0]
        print(f"Fazendo download de: {resource['name']}")
        extractor.download_resource(resource['url'], 'cadastro_fundos.csv')

def exemplo_exportacao():
    """Exemplo 5: Exportar metadados"""
    print("\n🔷 EXEMPLO 5: Exportar metadados\n")

    extractor = CVMDataExtractor()
    all_data = extractor.extract_all_resources(verbose=False)

    # Exportar para JSON e CSV
    extractor.export_to_json(all_data)
    extractor.export_to_csv(all_data)


def exemplo_dashboard():
    """Exemplo 6: Dashboard completo com rastreamento de mudanças"""
    print("\n" + "="*100)
    print(Colors.colorize("EXEMPLO 6: Dashboard Completo com Rastreamento de Mudanças", Colors.CYAN, bold=True))
    print("="*100 + "\n")

    # Inicializar extrator com output para arquivo texto
    extractor = CVMDataExtractor(output_file='cvm_dashboard.txt')

    # Carregar estado anterior
    print(Colors.colorize("Carregando estado anterior...", Colors.YELLOW))
    previous_state = extractor.load_state()

    if previous_state:
        print(Colors.colorize(f"Execução anterior: {format_timestamp(previous_state.get('last_run_timestamp', 'N/A'))}", Colors.GREEN))
    else:
        print(Colors.colorize("Nenhum estado anterior encontrado. Esta é a primeira execução.", Colors.YELLOW))

    print()

    # Extrair dados (com caching inteligente se houver estado anterior)
    all_data = extractor.extract_all_resources_smart(previous_state, verbose=True)

    print()

    # Detectar mudanças
    changes = extractor.detect_changes(all_data, previous_state)

    # Exibir dashboard
    extractor.print_dashboard(all_data, changes, previous_state)

    # Salvar estado para próxima execução
    print(Colors.colorize("Salvando estado atual...", Colors.YELLOW))
    extractor.save_state(all_data)

    # Exportar metadados
    print(Colors.colorize("Exportando dados...", Colors.YELLOW))
    extractor.export_to_json(all_data)
    extractor.export_to_csv(all_data)
    extractor.export_metadata_summary(all_data, changes)

    print()
    print(Colors.colorize("=" * 100, Colors.GREEN))
    print(Colors.colorize("Execução do dashboard concluída com sucesso!", Colors.GREEN, bold=True))
    print(Colors.colorize("=" * 100, Colors.GREEN))
    print()


if __name__ == "__main__":
    # Execute o exemplo que preferir:

    # extractor = CVMDataExtractor()
    # extractor.list_all_datasets()

    # exemplo_basico()              # Resumo completo (antigo)
    # exemplo_busca()               # Busca específica
    # exemplo_recursos_recentes()   # Últimos arquivos
    # exemplo_download()            # Baixar arquivo
    # exemplo_exportacao()          # Exportar metadados (antigo)

    exemplo_dashboard()             # Dashboard completo com rastreamento (RECOMENDADO)