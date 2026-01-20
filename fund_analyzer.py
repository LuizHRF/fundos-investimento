"""
Fund Analyzer Module

Downloads and analyzes Brazilian investment fund data from CVM Open Data Portal.
Provides fund comparison, filtering, and analysis capabilities.
"""

import csv
import io
import requests
from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field
import json
import sqlite3
from pathlib import Path


@dataclass
class Fund:
    """Unified fund data model"""
    cnpj: str
    name: str
    fund_type: str  # FI, FII, FIP, FIDC, FIAGRO, FIE
    status: str  # ATIVO, CANCELADA, etc.
    registration_date: Optional[str] = None
    cancel_date: Optional[str] = None

    # Manager and Administrator
    manager: Optional[str] = None
    manager_cnpj: Optional[str] = None
    administrator: Optional[str] = None
    admin_cnpj: Optional[str] = None
    custodian: Optional[str] = None
    auditor: Optional[str] = None

    # Classification
    anbima_class: Optional[str] = None
    classe: Optional[str] = None
    target_audience: Optional[str] = None  # PUBLICO_ALVO
    exclusive: Optional[bool] = None

    # Fees
    admin_fee: Optional[float] = None
    performance_fee: Optional[float] = None

    # Financial metrics
    net_worth: Optional[float] = None  # VL_PATRIM_LIQ
    net_worth_date: Optional[str] = None

    # Additional attributes
    metadata: Dict = field(default_factory=dict)

    def __str__(self):
        return f"Fund({self.cnpj}, {self.name}, {self.fund_type}, {self.status})"


class CVMDataDownloader:
    """Downloads and parses CVM CSV files"""

    BASE_URL = "https://dados.cvm.gov.br/dados"

    def __init__(self, cache_dir: str = "./data_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.session = requests.Session()

    def download_csv(self, url: str, use_cache: bool = True) -> List[Dict]:
        """
        Download and parse CSV file from CVM

        Args:
            url: Full URL to CSV file
            use_cache: Whether to use cached version if available

        Returns:
            List of dictionaries representing rows
        """
        # Create cache filename from URL
        cache_file = self.cache_dir / url.replace('/', '_').replace(':', '_')

        # Check cache
        if use_cache and cache_file.exists():
            cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            if cache_age < 3600:  # Cache valid for 1 hour
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

        # Download CSV
        print(f"Downloading: {url}")
        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        # Parse CSV with correct delimiter and encoding
        content = response.content.decode('latin-1')
        reader = csv.DictReader(io.StringIO(content), delimiter=';')
        data = list(reader)

        # Cache the result
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return data

    def get_fund_registration(self) -> List[Dict]:
        """Download fund registration data (cad_fi.csv)"""
        url = f"{self.BASE_URL}/FI/CAD/DADOS/cad_fi.csv"
        return self.download_csv(url)

    def get_fund_extract(self) -> List[Dict]:
        """Download fund extract/policies data (extrato_fi.csv)"""
        url = f"{self.BASE_URL}/FI/DOC/EXTRATO/DADOS/extrato_fi.csv"
        return self.download_csv(url)

    def get_monthly_profile(self, year_month: str) -> List[Dict]:
        """
        Download monthly profile data

        Args:
            year_month: Format YYYYMM (e.g., "202512")
        """
        url = f"{self.BASE_URL}/FI/DOC/PERFIL_MENSAL/DADOS/perfil_mensal_fi_{year_month}.csv"
        return self.download_csv(url)


class FundDatabase:
    """SQLite database for fund data storage"""

    def __init__(self, db_path: str = "./funds.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database schema"""
        cursor = self.conn.cursor()

        # Funds table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funds (
                cnpj TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                fund_type TEXT,
                status TEXT,
                registration_date TEXT,
                cancel_date TEXT,
                manager TEXT,
                manager_cnpj TEXT,
                administrator TEXT,
                admin_cnpj TEXT,
                custodian TEXT,
                auditor TEXT,
                anbima_class TEXT,
                classe TEXT,
                target_audience TEXT,
                exclusive INTEGER,
                admin_fee REAL,
                performance_fee REAL,
                net_worth REAL,
                net_worth_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Fund metadata (for flexible additional attributes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fund_metadata (
                cnpj TEXT,
                key TEXT,
                value TEXT,
                FOREIGN KEY(cnpj) REFERENCES funds(cnpj),
                PRIMARY KEY(cnpj, key)
            )
        """)

        # Fund history (track changes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fund_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cnpj TEXT,
                change_type TEXT,
                field_name TEXT,
                old_value TEXT,
                new_value TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(cnpj) REFERENCES funds(cnpj)
            )
        """)

        self.conn.commit()

    def insert_fund(self, fund: Fund) -> None:
        """Insert or update fund in database"""
        cursor = self.conn.cursor()

        # Check if fund exists
        cursor.execute("SELECT * FROM funds WHERE cnpj = ?", (fund.cnpj,))
        existing = cursor.fetchone()

        if existing:
            # Track changes
            self._track_changes(fund, dict(existing))

            # Update
            cursor.execute("""
                UPDATE funds SET
                    name = ?, fund_type = ?, status = ?,
                    registration_date = ?, cancel_date = ?,
                    manager = ?, manager_cnpj = ?,
                    administrator = ?, admin_cnpj = ?,
                    custodian = ?, auditor = ?,
                    anbima_class = ?, classe = ?,
                    target_audience = ?, exclusive = ?,
                    admin_fee = ?, performance_fee = ?,
                    net_worth = ?, net_worth_date = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE cnpj = ?
            """, (
                fund.name, fund.fund_type, fund.status,
                fund.registration_date, fund.cancel_date,
                fund.manager, fund.manager_cnpj,
                fund.administrator, fund.admin_cnpj,
                fund.custodian, fund.auditor,
                fund.anbima_class, fund.classe,
                fund.target_audience, 1 if fund.exclusive else 0,
                fund.admin_fee, fund.performance_fee,
                fund.net_worth, fund.net_worth_date,
                fund.cnpj
            ))
        else:
            # Insert
            cursor.execute("""
                INSERT INTO funds (
                    cnpj, name, fund_type, status,
                    registration_date, cancel_date,
                    manager, manager_cnpj,
                    administrator, admin_cnpj,
                    custodian, auditor,
                    anbima_class, classe,
                    target_audience, exclusive,
                    admin_fee, performance_fee,
                    net_worth, net_worth_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fund.cnpj, fund.name, fund.fund_type, fund.status,
                fund.registration_date, fund.cancel_date,
                fund.manager, fund.manager_cnpj,
                fund.administrator, fund.admin_cnpj,
                fund.custodian, fund.auditor,
                fund.anbima_class, fund.classe,
                fund.target_audience, 1 if fund.exclusive else 0,
                fund.admin_fee, fund.performance_fee,
                fund.net_worth, fund.net_worth_date
            ))

        # Store metadata
        for key, value in fund.metadata.items():
            cursor.execute("""
                INSERT OR REPLACE INTO fund_metadata (cnpj, key, value)
                VALUES (?, ?, ?)
            """, (fund.cnpj, key, str(value)))

        self.conn.commit()

    def _track_changes(self, new_fund: Fund, old_data: Dict) -> None:
        """Track changes between old and new fund data"""
        cursor = self.conn.cursor()

        # Fields to track
        fields_to_track = {
            'status': (old_data['status'], new_fund.status),
            'admin_fee': (old_data['admin_fee'], new_fund.admin_fee),
            'performance_fee': (old_data['performance_fee'], new_fund.performance_fee),
            'manager': (old_data['manager'], new_fund.manager),
            'administrator': (old_data['administrator'], new_fund.administrator),
        }

        for field, (old_val, new_val) in fields_to_track.items():
            if old_val != new_val:
                cursor.execute("""
                    INSERT INTO fund_history (cnpj, change_type, field_name, old_value, new_value)
                    VALUES (?, 'UPDATE', ?, ?, ?)
                """, (new_fund.cnpj, field, str(old_val), str(new_val)))

    def search_funds(self, filters: Dict) -> List[Dict]:
        """
        Search funds with filters

        Args:
            filters: Dict with filter criteria, e.g.:
                {'status': 'ATIVO', 'fund_type': 'FI', 'min_net_worth': 1000000}
        """
        query = "SELECT * FROM funds WHERE 1=1"
        params = []

        if 'status' in filters:
            query += " AND status = ?"
            params.append(filters['status'])

        if 'fund_type' in filters:
            query += " AND fund_type = ?"
            params.append(filters['fund_type'])

        if 'target_audience' in filters:
            query += " AND target_audience = ?"
            params.append(filters['target_audience'])

        if 'anbima_class' in filters:
            query += " AND anbima_class = ?"
            params.append(filters['anbima_class'])

        if 'min_net_worth' in filters:
            query += " AND net_worth >= ?"
            params.append(filters['min_net_worth'])

        if 'manager' in filters:
            query += " AND manager LIKE ?"
            params.append(f"%{filters['manager']}%")

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def get_fund_changes(self, cnpj: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get recent fund changes"""
        query = "SELECT * FROM fund_history"
        params = []

        if cnpj:
            query += " WHERE cnpj = ?"
            params.append(cnpj)

        query += " ORDER BY changed_at DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection"""
        self.conn.close()


class FundAnalyzer:
    """Main class for fund analysis and comparison"""

    def __init__(self, db_path: str = "./funds.db", cache_dir: str = "./data_cache"):
        self.downloader = CVMDataDownloader(cache_dir=cache_dir)
        self.database = FundDatabase(db_path=db_path)

    def load_fund_data(self) -> int:
        """
        Load fund data from CVM into database

        Returns:
            Number of funds loaded
        """
        print("Loading fund registration data...")
        cad_data = self.downloader.get_fund_registration()

        print("Loading fund extract/policies data...")
        extrato_data = self.downloader.get_fund_extract()

        # Index extrato by CNPJ for faster lookup
        extrato_by_cnpj = {}
        for row in extrato_data:
            cnpj = row.get('CNPJ_FUNDO_CLASSE', '').strip()
            if cnpj:
                extrato_by_cnpj[cnpj] = row

        # Process and merge data
        funds_loaded = 0
        for row in cad_data:
            cnpj = row.get('CNPJ_FUNDO', '').strip()
            if not cnpj:
                continue

            # Create Fund object
            fund = Fund(
                cnpj=cnpj,
                name=row.get('DENOM_SOCIAL', '').strip(),
                fund_type=row.get('TP_FUNDO', '').strip(),
                status=row.get('SIT', '').strip(),
                registration_date=row.get('DT_REG'),
                cancel_date=row.get('DT_CANCEL'),
                manager=row.get('GESTOR', '').strip() or None,
                manager_cnpj=row.get('CPF_CNPJ_GESTOR', '').strip() or None,
                administrator=row.get('ADMIN', '').strip() or None,
                admin_cnpj=row.get('CNPJ_ADMIN', '').strip() or None,
                custodian=row.get('CUSTODIANTE', '').strip() or None,
                auditor=row.get('AUDITOR', '').strip() or None,
                anbima_class=row.get('CLASSE_ANBIMA', '').strip() or None,
                classe=row.get('CLASSE', '').strip() or None,
                target_audience=row.get('PUBLICO_ALVO', '').strip() or None,
                exclusive=row.get('FUNDO_EXCLUSIVO') == 'S',
            )

            # Parse fees
            try:
                admin_fee_str = row.get('TAXA_ADM', '').replace(',', '.')
                if admin_fee_str:
                    fund.admin_fee = float(admin_fee_str)
            except (ValueError, AttributeError):
                pass

            try:
                perf_fee_str = row.get('TAXA_PERFM', '').replace(',', '.')
                if perf_fee_str:
                    fund.performance_fee = float(perf_fee_str)
            except (ValueError, AttributeError):
                pass

            # Parse net worth
            try:
                nw_str = row.get('VL_PATRIM_LIQ', '').replace(',', '.')
                if nw_str:
                    fund.net_worth = float(nw_str)
                    fund.net_worth_date = row.get('DT_PATRIM_LIQ')
            except (ValueError, AttributeError):
                pass

            # Merge extrato data if available
            if cnpj in extrato_by_cnpj:
                extrato_row = extrato_by_cnpj[cnpj]
                # Store extrato-specific fields in metadata
                fund.metadata['condom'] = extrato_row.get('CONDOM')
                fund.metadata['minimum_investment'] = extrato_row.get('APLIC_MIN')
                fund.metadata['redemption_days'] = extrato_row.get('QT_DIA_RESGATE_COTAS')
                fund.metadata['payment_days'] = extrato_row.get('QT_DIA_PAGTO_RESGATE')

            # Save to database
            self.database.insert_fund(fund)
            funds_loaded += 1

            if funds_loaded % 1000 == 0:
                print(f"  Loaded {funds_loaded} funds...")

        print(f"✓ Loaded {funds_loaded} funds into database")
        return funds_loaded

    def compare_funds(self, cnpj_list: List[str]) -> Dict:
        """
        Compare multiple funds side-by-side

        Args:
            cnpj_list: List of fund CNPJs to compare

        Returns:
            Dictionary with comparison data
        """
        funds = []
        for cnpj in cnpj_list:
            results = self.database.search_funds({'cnpj': cnpj})
            if results:
                funds.append(results[0])

        if not funds:
            return {"error": "No funds found"}

        comparison = {
            "funds": funds,
            "comparison_date": datetime.now().isoformat(),
            "fields": {
                "Basic Info": ["name", "fund_type", "status", "anbima_class"],
                "Fees": ["admin_fee", "performance_fee"],
                "Management": ["manager", "administrator"],
                "Financial": ["net_worth", "net_worth_date"],
            }
        }

        return comparison

    def get_statistics(self) -> Dict:
        """Get overall fund statistics"""
        cursor = self.database.conn.cursor()

        stats = {}

        # Total funds
        cursor.execute("SELECT COUNT(*) as total FROM funds")
        stats['total_funds'] = cursor.fetchone()[0]

        # Active funds (using correct status value)
        cursor.execute("SELECT COUNT(*) as active FROM funds WHERE status = 'EM FUNCIONAMENTO NORMAL'")
        stats['active_funds'] = cursor.fetchone()[0]

        # By status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM funds
            GROUP BY status
            ORDER BY count DESC
        """)
        stats['by_status'] = {row[0]: row[1] for row in cursor.fetchall()}

        # By fund type
        cursor.execute("""
            SELECT fund_type, COUNT(*) as count
            FROM funds
            WHERE status = 'EM FUNCIONAMENTO NORMAL'
            GROUP BY fund_type
            ORDER BY count DESC
        """)
        stats['by_type'] = {row[0]: row[1] for row in cursor.fetchall()}

        # By ANBIMA class
        cursor.execute("""
            SELECT anbima_class, COUNT(*) as count
            FROM funds
            WHERE status = 'EM FUNCIONAMENTO NORMAL' AND anbima_class IS NOT NULL
            GROUP BY anbima_class
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['top_anbima_classes'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Top managers
        cursor.execute("""
            SELECT manager, COUNT(*) as count, SUM(net_worth) as total_aum
            FROM funds
            WHERE status = 'EM FUNCIONAMENTO NORMAL' AND manager IS NOT NULL
            GROUP BY manager
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['top_managers'] = [
            {"manager": row[0], "fund_count": row[1], "total_aum": row[2]}
            for row in cursor.fetchall()
        ]

        return stats

    def export_comparison_csv(self, cnpj_list: List[str], output_file: str):
        """Export fund comparison to CSV"""
        import csv

        comparison = self.compare_funds(cnpj_list)
        if "error" in comparison:
            print(f"Error: {comparison['error']}")
            return

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(['Field'] + [f['name'] for f in comparison['funds']])

            # Write each field category
            for category, fields in comparison['fields'].items():
                writer.writerow([f"--- {category} ---"])
                for field in fields:
                    row = [field]
                    for fund in comparison['funds']:
                        row.append(fund.get(field, 'N/A'))
                    writer.writerow(row)

        print(f"✓ Comparison exported to {output_file}")


def main():
    """Example usage"""
    analyzer = FundAnalyzer()

    # Load data
    print("=" * 60)
    print("Loading fund data from CVM...")
    print("=" * 60)
    count = analyzer.load_fund_data()

    # Show statistics
    print("\n" + "=" * 60)
    print("Fund Statistics")
    print("=" * 60)
    stats = analyzer.get_statistics()
    print(f"Total funds in database: {stats['total_funds']}")
    print(f"Active funds (EM FUNCIONAMENTO NORMAL): {stats['active_funds']}")

    print(f"\nBy status:")
    for status, count in list(stats['by_status'].items())[:5]:
        print(f"  {status}: {count}")

    print(f"\nActive funds by type:")
    for fund_type, count in stats['by_type'].items():
        print(f"  {fund_type}: {count}")

    if stats['top_anbima_classes']:
        print(f"\nTop ANBIMA classes (active funds):")
        for anbima_class, count in list(stats['top_anbima_classes'].items())[:5]:
            print(f"  {anbima_class}: {count}")

    # Example search - all funds regardless of status
    print("\n" + "=" * 60)
    print("Sample: Recent funds (any status)...")
    print("=" * 60)
    results = analyzer.database.search_funds({})
    print(f"Total funds in database: {len(results)}")
    if results:
        print("\nFirst 5 funds:")
        for fund in results[:5]:
            print(f"  - {fund['name']}")
            print(f"    CNPJ: {fund['cnpj']}")
            print(f"    Status: {fund['status']}")
            print(f"    Type: {fund['fund_type']}")
            print(f"    Manager: {fund['manager']}")
            if fund['admin_fee']:
                print(f"    Admin Fee: {fund['admin_fee']}%")
            print()

    # Example: Active funds only
    print("=" * 60)
    print("Active funds only (EM FUNCIONAMENTO NORMAL)...")
    print("=" * 60)
    active_results = analyzer.database.search_funds({
        'status': 'EM FUNCIONAMENTO NORMAL'
    })
    print(f"Found {len(active_results)} active funds")
    if active_results:
        print("\nFirst 5 active funds:")
        for fund in active_results[:5]:
            print(f"  - {fund['name']}")
            print(f"    CNPJ: {fund['cnpj']}")
            print(f"    Type: {fund['fund_type']}")
            print(f"    ANBIMA Class: {fund['anbima_class']}")
            print(f"    Manager: {fund['manager']}")
            print(f"    Administrator: {fund['administrator']}")
            if fund['admin_fee']:
                print(f"    Admin Fee: {fund['admin_fee']}%")
            if fund['net_worth']:
                print(f"    Net Worth: R$ {fund['net_worth']:,.2f}")
            print()


if __name__ == "__main__":
    main()
