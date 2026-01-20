"""
Módulo Analisador de Fundos

Baixa e analisa dados de fundos de investimento brasileiros do Portal de Dados Abertos da CVM.
Fornece funcionalidades de comparação, filtragem e análise de fundos.
"""

import csv
import io
import requests
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import json
import sqlite3
from pathlib import Path


@dataclass
class Fundo:
    """Modelo unificado de dados de fundo"""
    cnpj: str
    nome: str
    tipo_fundo: str  # FI, FII, FIP, FIDC, FIAGRO, FIE
    situacao: str  # EM FUNCIONAMENTO NORMAL, CANCELADA, etc.
    data_registro: Optional[str] = None
    data_cancelamento: Optional[str] = None

    # Gestor e Administrador
    gestor: Optional[str] = None
    cnpj_gestor: Optional[str] = None
    administrador: Optional[str] = None
    cnpj_admin: Optional[str] = None
    custodiante: Optional[str] = None
    auditor: Optional[str] = None

    # Classificação
    classe_anbima: Optional[str] = None
    classe: Optional[str] = None
    publico_alvo: Optional[str] = None
    exclusivo: Optional[bool] = None

    # Taxas
    taxa_admin: Optional[float] = None
    taxa_performance: Optional[float] = None

    # Métricas financeiras
    patrimonio_liquido: Optional[float] = None
    data_patrimonio: Optional[str] = None

    # Atributos adicionais
    metadados: Dict = field(default_factory=dict)

    def __str__(self):
        return f"Fundo({self.cnpj}, {self.nome}, {self.tipo_fundo}, {self.situacao})"


class CVMDownloader:
    """Baixa e processa arquivos CSV da CVM"""

    BASE_URL = "https://dados.cvm.gov.br/dados"

    def __init__(self, diretorio_cache: str = "./output/cache"):
        self.diretorio_cache = Path(diretorio_cache)
        self.diretorio_cache.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()

    def baixar_csv(self, url: str, usar_cache: bool = True) -> List[Dict]:
        """
        Baixa e processa arquivo CSV da CVM

        Args:
            url: URL completa do arquivo CSV
            usar_cache: Se deve usar versão em cache se disponível

        Returns:
            Lista de dicionários representando as linhas
        """
        # Criar nome do arquivo de cache a partir da URL
        arquivo_cache = self.diretorio_cache / url.replace('/', '_').replace(':', '_')

        # Verificar cache
        if usar_cache and arquivo_cache.exists():
            idade_cache = datetime.now().timestamp() - arquivo_cache.stat().st_mtime
            if idade_cache < 3600:  # Cache válido por 1 hora
                with open(arquivo_cache, 'r', encoding='utf-8') as f:
                    return json.load(f)

        # Baixar CSV
        print(f"Baixando: {url}")
        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        # Processar CSV com delimitador e encoding corretos
        conteudo = response.content.decode('latin-1')
        reader = csv.DictReader(io.StringIO(conteudo), delimiter=';')
        dados = list(reader)

        # Salvar em cache
        with open(arquivo_cache, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

        return dados

    def obter_cadastro_fundos(self) -> List[Dict]:
        """Baixa dados cadastrais dos fundos (cad_fi.csv)"""
        url = f"{self.BASE_URL}/FI/CAD/DADOS/cad_fi.csv"
        return self.baixar_csv(url)

    def obter_extrato_fundos(self) -> List[Dict]:
        """Baixa dados de extrato/políticas dos fundos (extrato_fi.csv)"""
        url = f"{self.BASE_URL}/FI/DOC/EXTRATO/DADOS/extrato_fi.csv"
        return self.baixar_csv(url)

    def obter_perfil_mensal(self, ano_mes: str) -> List[Dict]:
        """
        Baixa dados do perfil mensal

        Args:
            ano_mes: Formato AAAAMM (ex: "202512")
        """
        url = f"{self.BASE_URL}/FI/DOC/PERFIL_MENSAL/DADOS/perfil_mensal_fi_{ano_mes}.csv"
        return self.baixar_csv(url)


class BancoDadosFundos:
    """Banco de dados SQLite para armazenamento de dados de fundos"""

    def __init__(self, caminho_db: str = "./output/fundos.db"):
        Path(caminho_db).parent.mkdir(parents=True, exist_ok=True)
        self.caminho_db = caminho_db
        self.conn = sqlite3.connect(caminho_db)
        self.conn.row_factory = sqlite3.Row
        self._criar_tabelas()

    def _criar_tabelas(self):
        """Cria esquema do banco de dados"""
        cursor = self.conn.cursor()

        # Tabela de fundos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fundos (
                cnpj TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                tipo_fundo TEXT,
                situacao TEXT,
                data_registro TEXT,
                data_cancelamento TEXT,
                gestor TEXT,
                cnpj_gestor TEXT,
                administrador TEXT,
                cnpj_admin TEXT,
                custodiante TEXT,
                auditor TEXT,
                classe_anbima TEXT,
                classe TEXT,
                publico_alvo TEXT,
                exclusivo INTEGER,
                taxa_admin REAL,
                taxa_performance REAL,
                patrimonio_liquido REAL,
                data_patrimonio TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela de metadados dos fundos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fundos_metadados (
                cnpj TEXT,
                chave TEXT,
                valor TEXT,
                FOREIGN KEY(cnpj) REFERENCES fundos(cnpj),
                PRIMARY KEY(cnpj, chave)
            )
        """)

        # Tabela de histórico de mudanças
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fundos_historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cnpj TEXT,
                tipo_mudanca TEXT,
                campo TEXT,
                valor_anterior TEXT,
                valor_novo TEXT,
                alterado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(cnpj) REFERENCES fundos(cnpj)
            )
        """)

        self.conn.commit()

    def inserir_fundo(self, fundo: Fundo) -> None:
        """Insere ou atualiza fundo no banco de dados"""
        cursor = self.conn.cursor()

        # Verificar se fundo existe
        cursor.execute("SELECT * FROM fundos WHERE cnpj = ?", (fundo.cnpj,))
        existente = cursor.fetchone()

        if existente:
            # Rastrear mudanças
            self._rastrear_mudancas(fundo, dict(existente))

            # Atualizar
            cursor.execute("""
                UPDATE fundos SET
                    nome = ?, tipo_fundo = ?, situacao = ?,
                    data_registro = ?, data_cancelamento = ?,
                    gestor = ?, cnpj_gestor = ?,
                    administrador = ?, cnpj_admin = ?,
                    custodiante = ?, auditor = ?,
                    classe_anbima = ?, classe = ?,
                    publico_alvo = ?, exclusivo = ?,
                    taxa_admin = ?, taxa_performance = ?,
                    patrimonio_liquido = ?, data_patrimonio = ?,
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE cnpj = ?
            """, (
                fundo.nome, fundo.tipo_fundo, fundo.situacao,
                fundo.data_registro, fundo.data_cancelamento,
                fundo.gestor, fundo.cnpj_gestor,
                fundo.administrador, fundo.cnpj_admin,
                fundo.custodiante, fundo.auditor,
                fundo.classe_anbima, fundo.classe,
                fundo.publico_alvo, 1 if fundo.exclusivo else 0,
                fundo.taxa_admin, fundo.taxa_performance,
                fundo.patrimonio_liquido, fundo.data_patrimonio,
                fundo.cnpj
            ))
        else:
            # Inserir
            cursor.execute("""
                INSERT INTO fundos (
                    cnpj, nome, tipo_fundo, situacao,
                    data_registro, data_cancelamento,
                    gestor, cnpj_gestor,
                    administrador, cnpj_admin,
                    custodiante, auditor,
                    classe_anbima, classe,
                    publico_alvo, exclusivo,
                    taxa_admin, taxa_performance,
                    patrimonio_liquido, data_patrimonio
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fundo.cnpj, fundo.nome, fundo.tipo_fundo, fundo.situacao,
                fundo.data_registro, fundo.data_cancelamento,
                fundo.gestor, fundo.cnpj_gestor,
                fundo.administrador, fundo.cnpj_admin,
                fundo.custodiante, fundo.auditor,
                fundo.classe_anbima, fundo.classe,
                fundo.publico_alvo, 1 if fundo.exclusivo else 0,
                fundo.taxa_admin, fundo.taxa_performance,
                fundo.patrimonio_liquido, fundo.data_patrimonio
            ))

        # Salvar metadados
        for chave, valor in fundo.metadados.items():
            cursor.execute("""
                INSERT OR REPLACE INTO fundos_metadados (cnpj, chave, valor)
                VALUES (?, ?, ?)
            """, (fundo.cnpj, chave, str(valor)))

        self.conn.commit()

    def _rastrear_mudancas(self, novo_fundo: Fundo, dados_antigos: Dict) -> None:
        """Rastreia mudanças entre dados antigos e novos do fundo"""
        cursor = self.conn.cursor()

        # Campos a rastrear
        campos_rastrear = {
            'situacao': (dados_antigos['situacao'], novo_fundo.situacao),
            'taxa_admin': (dados_antigos['taxa_admin'], novo_fundo.taxa_admin),
            'taxa_performance': (dados_antigos['taxa_performance'], novo_fundo.taxa_performance),
            'gestor': (dados_antigos['gestor'], novo_fundo.gestor),
            'administrador': (dados_antigos['administrador'], novo_fundo.administrador),
        }

        for campo, (val_antigo, val_novo) in campos_rastrear.items():
            if val_antigo != val_novo:
                cursor.execute("""
                    INSERT INTO fundos_historico (cnpj, tipo_mudanca, campo, valor_anterior, valor_novo)
                    VALUES (?, 'ATUALIZACAO', ?, ?, ?)
                """, (novo_fundo.cnpj, campo, str(val_antigo), str(val_novo)))

    def buscar_fundos(self, filtros: Dict) -> List[Dict]:
        """
        Busca fundos com filtros

        Args:
            filtros: Dicionário com critérios de filtro, ex:
                {'situacao': 'EM FUNCIONAMENTO NORMAL', 'tipo_fundo': 'FI', 'patrimonio_min': 1000000}
        """
        query = "SELECT * FROM fundos WHERE 1=1"
        params = []

        if 'situacao' in filtros:
            query += " AND situacao = ?"
            params.append(filtros['situacao'])

        if 'tipo_fundo' in filtros:
            query += " AND tipo_fundo = ?"
            params.append(filtros['tipo_fundo'])

        if 'publico_alvo' in filtros:
            query += " AND publico_alvo = ?"
            params.append(filtros['publico_alvo'])

        if 'classe_anbima' in filtros:
            query += " AND classe_anbima = ?"
            params.append(filtros['classe_anbima'])

        if 'patrimonio_min' in filtros:
            query += " AND patrimonio_liquido >= ?"
            params.append(filtros['patrimonio_min'])

        if 'gestor' in filtros:
            query += " AND gestor LIKE ?"
            params.append(f"%{filtros['gestor']}%")

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def obter_mudancas(self, cnpj: Optional[str] = None, limite: int = 100) -> List[Dict]:
        """Obtém mudanças recentes de fundos"""
        query = "SELECT * FROM fundos_historico"
        params = []

        if cnpj:
            query += " WHERE cnpj = ?"
            params.append(cnpj)

        query += " ORDER BY alterado_em DESC LIMIT ?"
        params.append(limite)

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def fechar(self):
        """Fecha conexão com o banco de dados"""
        self.conn.close()


class AnalisadorFundos:
    """Classe principal para análise e comparação de fundos"""

    def __init__(self, caminho_db: str = "./output/fundos.db", diretorio_cache: str = "./output/cache"):
        self.downloader = CVMDownloader(diretorio_cache=diretorio_cache)
        self.banco = BancoDadosFundos(caminho_db=caminho_db)

    def carregar_dados(self) -> int:
        """
        Carrega dados de fundos da CVM no banco de dados

        Returns:
            Número de fundos carregados
        """
        print("Carregando dados cadastrais dos fundos...")
        dados_cadastro = self.downloader.obter_cadastro_fundos()

        print("Carregando dados de extrato/políticas dos fundos...")
        dados_extrato = self.downloader.obter_extrato_fundos()

        # Indexar extrato por CNPJ para busca mais rápida
        extrato_por_cnpj = {}
        for linha in dados_extrato:
            cnpj = linha.get('CNPJ_FUNDO_CLASSE', '').strip()
            if cnpj:
                extrato_por_cnpj[cnpj] = linha

        # Processar e mesclar dados
        fundos_carregados = 0
        for linha in dados_cadastro:
            cnpj = linha.get('CNPJ_FUNDO', '').strip()
            if not cnpj:
                continue

            # Criar objeto Fundo
            fundo = Fundo(
                cnpj=cnpj,
                nome=linha.get('DENOM_SOCIAL', '').strip(),
                tipo_fundo=linha.get('TP_FUNDO', '').strip(),
                situacao=linha.get('SIT', '').strip(),
                data_registro=linha.get('DT_REG'),
                data_cancelamento=linha.get('DT_CANCEL'),
                gestor=linha.get('GESTOR', '').strip() or None,
                cnpj_gestor=linha.get('CPF_CNPJ_GESTOR', '').strip() or None,
                administrador=linha.get('ADMIN', '').strip() or None,
                cnpj_admin=linha.get('CNPJ_ADMIN', '').strip() or None,
                custodiante=linha.get('CUSTODIANTE', '').strip() or None,
                auditor=linha.get('AUDITOR', '').strip() or None,
                classe_anbima=linha.get('CLASSE_ANBIMA', '').strip() or None,
                classe=linha.get('CLASSE', '').strip() or None,
                publico_alvo=linha.get('PUBLICO_ALVO', '').strip() or None,
                exclusivo=linha.get('FUNDO_EXCLUSIVO') == 'S',
            )

            # Processar taxas
            try:
                taxa_admin_str = linha.get('TAXA_ADM', '').replace(',', '.')
                if taxa_admin_str:
                    fundo.taxa_admin = float(taxa_admin_str)
            except (ValueError, AttributeError):
                pass

            try:
                taxa_perf_str = linha.get('TAXA_PERFM', '').replace(',', '.')
                if taxa_perf_str:
                    fundo.taxa_performance = float(taxa_perf_str)
            except (ValueError, AttributeError):
                pass

            # Processar patrimônio líquido
            try:
                pl_str = linha.get('VL_PATRIM_LIQ', '').replace(',', '.')
                if pl_str:
                    fundo.patrimonio_liquido = float(pl_str)
                    fundo.data_patrimonio = linha.get('DT_PATRIM_LIQ')
            except (ValueError, AttributeError):
                pass

            # Mesclar dados do extrato se disponível
            if cnpj in extrato_por_cnpj:
                extrato_linha = extrato_por_cnpj[cnpj]
                fundo.metadados['condominio'] = extrato_linha.get('CONDOM')
                fundo.metadados['aplicacao_minima'] = extrato_linha.get('APLIC_MIN')
                fundo.metadados['dias_resgate'] = extrato_linha.get('QT_DIA_RESGATE_COTAS')
                fundo.metadados['dias_pagamento'] = extrato_linha.get('QT_DIA_PAGTO_RESGATE')

            # Salvar no banco de dados
            self.banco.inserir_fundo(fundo)
            fundos_carregados += 1

            if fundos_carregados % 1000 == 0:
                print(f"  {fundos_carregados} fundos carregados...")

        print(f"✓ {fundos_carregados} fundos carregados no banco de dados")
        return fundos_carregados

    def comparar_fundos(self, lista_cnpj: List[str]) -> Dict:
        """
        Compara múltiplos fundos lado a lado

        Args:
            lista_cnpj: Lista de CNPJs dos fundos a comparar

        Returns:
            Dicionário com dados da comparação
        """
        fundos = []
        for cnpj in lista_cnpj:
            resultados = self.banco.buscar_fundos({'cnpj': cnpj})
            if resultados:
                fundos.append(resultados[0])

        if not fundos:
            return {"erro": "Nenhum fundo encontrado"}

        comparacao = {
            "fundos": fundos,
            "data_comparacao": datetime.now().isoformat(),
            "campos": {
                "Informações Básicas": ["nome", "tipo_fundo", "situacao", "classe_anbima"],
                "Taxas": ["taxa_admin", "taxa_performance"],
                "Gestão": ["gestor", "administrador"],
                "Financeiro": ["patrimonio_liquido", "data_patrimonio"],
            }
        }

        return comparacao

    def obter_estatisticas(self) -> Dict:
        """Obtém estatísticas gerais dos fundos"""
        cursor = self.banco.conn.cursor()

        stats = {}

        # Total de fundos
        cursor.execute("SELECT COUNT(*) as total FROM fundos")
        stats['total_fundos'] = cursor.fetchone()[0]

        # Fundos ativos
        cursor.execute("SELECT COUNT(*) as ativos FROM fundos WHERE situacao = 'EM FUNCIONAMENTO NORMAL'")
        stats['fundos_ativos'] = cursor.fetchone()[0]

        # Por situação
        cursor.execute("""
            SELECT situacao, COUNT(*) as qtd
            FROM fundos
            GROUP BY situacao
            ORDER BY qtd DESC
        """)
        stats['por_situacao'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Por tipo de fundo
        cursor.execute("""
            SELECT tipo_fundo, COUNT(*) as qtd
            FROM fundos
            WHERE situacao = 'EM FUNCIONAMENTO NORMAL'
            GROUP BY tipo_fundo
            ORDER BY qtd DESC
        """)
        stats['por_tipo'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Por classe ANBIMA
        cursor.execute("""
            SELECT classe_anbima, COUNT(*) as qtd
            FROM fundos
            WHERE situacao = 'EM FUNCIONAMENTO NORMAL' AND classe_anbima IS NOT NULL
            GROUP BY classe_anbima
            ORDER BY qtd DESC
            LIMIT 10
        """)
        stats['top_classes_anbima'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Maiores gestores
        cursor.execute("""
            SELECT gestor, COUNT(*) as qtd, SUM(patrimonio_liquido) as pl_total
            FROM fundos
            WHERE situacao = 'EM FUNCIONAMENTO NORMAL' AND gestor IS NOT NULL
            GROUP BY gestor
            ORDER BY qtd DESC
            LIMIT 10
        """)
        stats['maiores_gestores'] = [
            {"gestor": row[0], "qtd_fundos": row[1], "pl_total": row[2]}
            for row in cursor.fetchall()
        ]

        return stats

    def exportar_comparacao_csv(self, lista_cnpj: List[str], arquivo_saida: str):
        """Exporta comparação de fundos para CSV"""
        comparacao = self.comparar_fundos(lista_cnpj)
        if "erro" in comparacao:
            print(f"Erro: {comparacao['erro']}")
            return

        with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Cabeçalho
            writer.writerow(['Campo'] + [fundo['nome'] for fundo in comparacao['fundos']])

            # Escrever cada categoria de campo
            for categoria, campos in comparacao['campos'].items():
                writer.writerow([f"--- {categoria} ---"])
                for campo in campos:
                    linha = [campo]
                    for fundo in comparacao['fundos']:
                        linha.append(fundo.get(campo, 'N/A'))
                    writer.writerow(linha)

        print(f"✓ Comparação exportada para {arquivo_saida}")
