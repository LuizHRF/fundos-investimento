# CVM Fundos de Investimento

Consolide dados de fundos de investimento brasileiros usando dados do Portal de Dados Abertos da CVM (Resolução CVM 175).

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
python main.py                    # Consolida dados (usa cache local)
python main.py consolidate        # Mesmo que acima
python main.py consolidate --force  # Força re-download do servidor CVM
```

> **Nota**: O script usa cache local. Para obter dados atualizados do servidor CVM, use `--force`. A CVM atualiza os dados diariamente às 08:00h (horário de Brasília).

## O Que Faz

Baixa e processa o arquivo `registro_fundo_classe.zip` da CVM contendo:
- **86.878 fundos** (33.475 em funcionamento)
- **35.411 classes de cotas** com classificação ANBIMA
- **Dados ESG** para ~700 classes

Exporta dois arquivos CSV:
- `output/fundos_principais.csv` - Um fundo por linha
- `output/fundos_classes.csv` - Uma classe por linha

## Estrutura

```
fundos-investimento/
├── main.py                  # Ponto de entrada
├── src/
│   └── consolidador/        # Pacote de consolidação
│       ├── config.py        # URLs e mapeamentos
│       ├── downloader.py    # Download com cache
│       ├── consolidator.py  # Orquestrador
│       ├── merger.py        # Merge Fundo → Classe
│       ├── exporter.py      # Exportação CSV
│       └── parsers/
│           └── rcvm175.py   # Parser RCVM175
└── output/
    ├── fundos_principais.csv  # ~87k fundos
    ├── fundos_classes.csv     # ~35k classes
    └── cache/                 # Cache de downloads
```

## Dados Disponíveis

### Por Tipo de Fundo

| Tipo | Nome | Quantidade |
|------|------|------------|
| FI | Fundos de Investimento | 60.444 |
| FIDC | Direitos Creditórios | 7.135 |
| FIF | Fundos de Fundos | 5.229 |
| FIP | Participações (Private Equity) | 4.203 |
| FII | Imobiliários | 2.034 |
| FIAGRO | Cadeias Agroindustriais | 272 |

### Por Status

| Status | Quantidade | % |
|--------|------------|---|
| Em Funcionamento Normal | 33.475 | 38,6% |
| Cancelado | 50.528 | 58,2% |
| Fase Pré-Operacional | 2.221 | 2,6% |
| Em Liquidação | 638 | 0,7% |

## Fonte dos Dados

- **Portal**: https://dados.cvm.gov.br
- **Arquivo**: `registro_fundo_classe.zip` (Resolução CVM 175)
- **Atualização**: Diária

---

**Versão**: 5.0 | **Atualização**: Janeiro 2026
