# Módulos de análise de fundos de investimento CVM
# Dashboard de monitoramento e comparador de fundos

from .analisador_fundos import Fundo, CVMDownloader, BancoDadosFundos, AnalisadorFundos
from .comparador_cli import (
    exibir_estatisticas,
    exibir_comparacao,
    exibir_mudancas,
    demonstracao_completa,
    main_comparador
)
from .dashboard_cvm import CVMDataExtractor, Colors, main_dashboard

__all__ = [
    # Analisador de Fundos
    'Fundo',
    'CVMDownloader',
    'BancoDadosFundos',
    'AnalisadorFundos',
    # CLI do Comparador
    'exibir_estatisticas',
    'exibir_comparacao',
    'exibir_mudancas',
    'demonstracao_completa',
    'main_comparador',
    # Dashboard CVM
    'CVMDataExtractor',
    'Colors',
    'main_dashboard'
]
