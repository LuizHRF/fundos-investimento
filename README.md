# CVM Fundos de Investimento

Monitore e analise fundos de investimento brasileiros usando dados do Portal de Dados Abertos da CVM.

## Instalação

```bash
# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt
```

## Uso

```bash
python main.py          # Dashboard de monitoramento CVM
python main.py funds    # Tabela comparativa de fundos
```

### Dashboard (`python main.py`)

Monitora os 22 datasets de fundos da CVM:
- Exibe status de todos os recursos (CSV, ZIP, etc.)
- Detecta mudanças desde a última execução
- Organiza por tipo de fundo (FI, FII, FIP, FIDC, FIAGRO, FIE)
- Salva estado em SQLite para rastreamento

### Comparação de Fundos (`python main.py funds`)

Gera tabela comparativa com todos os fundos:
- Baixa dados cadastrais da CVM (cad_fi.csv)
- Exporta para `output/comparacao_fundos.csv`
- Exibe estatísticas (total, ativos, por tipo, patrimônio)

## Estrutura

```
fundos-investimento/
├── main.py                  # Ponto de entrada
├── src/
│   ├── analisador_fundos.py # Comparação de fundos
│   ├── dashboard_cvm.py     # Dashboard de monitoramento
│   └── storage.py           # Armazenamento SQLite
└── output/
    ├── comparacao_fundos.csv  # Tabela de fundos
    ├── cvm_data.db            # Estado do dashboard
    └── cache/                 # Cache de downloads
```

## Dados Monitorados

| Tipo | Datasets | Descrição |
|------|----------|-----------|
| FI | 10 | Fundos de Investimento (informes, balancetes) |
| FII | 4 | Fundos Imobiliários |
| FIP | 2 | Fundos de Participações |
| FIDC | 1 | Direitos Creditórios |
| FIAGRO | 1 | Cadeias Agroindustriais |
| FIE | 3 | Fundos Estruturados |

## Fonte dos Dados

- **Portal**: https://dados.cvm.gov.br
- **Grupo**: fundos-de-investimento
- **Atualização**: Diária (08:00 Brasília)

---

**Versão**: 4.0 | **Atualização**: Janeiro 2026
