"""
Armazenamento SQLite para dados CVM
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path("./output/cvm_data.db")


def get_connection():
    """Retorna conexão com o banco de dados"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _init_tables(conn)
    return conn


def _init_tables(conn):
    """Cria tabelas se não existirem"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY,
            title TEXT,
            metadata_modified TEXT,
            num_resources INTEGER,
            url TEXT,
            data JSON,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS resources (
            id TEXT PRIMARY KEY,
            dataset_id TEXT,
            name TEXT,
            format TEXT,
            url TEXT,
            size INTEGER,
            last_modified TEXT,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id)
        );
        CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS changes_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            change_type TEXT,
            entity_type TEXT,
            entity_id TEXT,
            details TEXT,
            detected_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()


def save_state(all_data: dict):
    """Salva estado atual no banco de dados"""
    conn = get_connection()
    cur = conn.cursor()

    # Salvar timestamp
    cur.execute("INSERT OR REPLACE INTO state (key, value, updated_at) VALUES (?, ?, ?)",
                ("last_run", datetime.now().isoformat(), datetime.now().isoformat()))

    # Salvar datasets e recursos
    for dataset_id, info in all_data.items():
        cur.execute("""
            INSERT OR REPLACE INTO datasets (id, title, metadata_modified, num_resources, url, data, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (dataset_id, info.get('title'), info.get('metadata_modified'),
              info.get('num_resources'), info.get('url'), json.dumps(info), datetime.now().isoformat()))

        for res in info.get('resources', []):
            cur.execute("""
                INSERT OR REPLACE INTO resources (id, dataset_id, name, format, url, size, last_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (res['id'], dataset_id, res.get('name'), res.get('format'),
                  res.get('url'), res.get('size'), res.get('last_modified')))

    conn.commit()
    conn.close()
    print(f"✓ Estado salvo em: {DB_PATH}")


def load_state() -> dict:
    """Carrega estado anterior do banco de dados no formato esperado"""
    conn = get_connection()
    cur = conn.cursor()

    state = {'datasets': {}}

    # Carregar datasets
    cur.execute("SELECT id, metadata_modified, num_resources FROM datasets")
    for row in cur.fetchall():
        dataset_id = row['id']
        state['datasets'][dataset_id] = {
            'metadata_modified': row['metadata_modified'],
            'num_resources': row['num_resources'],
            'resources': {}
        }

    # Carregar recursos
    cur.execute("SELECT id, dataset_id, name, format, size, last_modified FROM resources")
    for row in cur.fetchall():
        dataset_id = row['dataset_id']
        if dataset_id in state['datasets']:
            state['datasets'][dataset_id]['resources'][row['id']] = {
                'name': row['name'],
                'format': row['format'],
                'size': row['size'],
                'last_modified': row['last_modified']
            }

    # Carregar timestamp
    cur.execute("SELECT value FROM state WHERE key = 'last_run'")
    row = cur.fetchone()
    if row:
        state['last_run_timestamp'] = row['value']

    conn.close()
    return state


def log_changes(changes: dict):
    """Registra mudanças detectadas"""
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now().isoformat()

    for change_type in ['new_datasets', 'modified_datasets', 'deleted_datasets']:
        for item in changes.get(change_type, []):
            cur.execute("INSERT INTO changes_log (change_type, entity_type, entity_id, detected_at) VALUES (?, ?, ?, ?)",
                        (change_type, 'dataset', item if isinstance(item, str) else item.get('id', str(item)), now))

    for change_type in ['new_resources', 'modified_resources', 'deleted_resources']:
        for item in changes.get(change_type, []):
            cur.execute("INSERT INTO changes_log (change_type, entity_type, entity_id, details, detected_at) VALUES (?, ?, ?, ?, ?)",
                        (change_type, 'resource', item.get('resource_id', ''), json.dumps(item), now))

    conn.commit()
    conn.close()


def get_summary() -> dict:
    """Retorna resumo estatístico do banco"""
    conn = get_connection()
    cur = conn.cursor()

    summary = {}
    cur.execute("SELECT COUNT(*) FROM datasets")
    summary['total_datasets'] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM resources")
    summary['total_resources'] = cur.fetchone()[0]

    cur.execute("SELECT format, COUNT(*) as cnt FROM resources GROUP BY format ORDER BY cnt DESC")
    summary['formats'] = {row['format']: row['cnt'] for row in cur.fetchall()}

    cur.execute("SELECT value FROM state WHERE key = 'last_run'")
    row = cur.fetchone()
    summary['last_run'] = row['value'] if row else None

    conn.close()
    return summary
