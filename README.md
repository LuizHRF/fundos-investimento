# CVM Fundos de Investimento - Dashboard

Monitore e acompanhe os dados de fundos de investimento brasileiros do Portal de Dados Abertos da CVM (Comissão de Valores Mobiliários).

## Funcionalidades

- **Dashboard Completo**: Visualização de todos os conjuntos de dados de fundos organizados por tipo
- **Rastreamento de Mudanças**: Detecta automaticamente novos datasets/recursos, modificações e exclusões entre execuções
- **Cache Inteligente**: Busca apenas dados modificados da API (15x mais rápido em execuções subsequentes!)
- **Multiplataforma**: Funciona no Windows, Linux e macOS
- **Múltiplos Formatos**: Saída no console, arquivo texto, JSON e CSV
- **Visual com Cores**: Terminal colorido com indicadores de status para fácil leitura

## Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (instalador de pacotes Python)

### Configuração

1. Clone ou faça download deste repositório

2. Crie um ambiente virtual:
```bash
python -m venv .venv
```

3. Ative o ambiente virtual:

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows:**
```cmd
.venv\Scripts\activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

### Início Rápido

O projeto oferece duas ferramentas principais através de um ponto de entrada unificado:

**Linux/macOS:**
```bash
source .venv/bin/activate
python main.py              # Comparador de fundos (padrão)
python main.py dashboard    # Dashboard de monitoramento
```

**Windows:**
```cmd
.venv\Scripts\activate
python main.py              # Comparador de fundos (padrão)
python main.py dashboard    # Dashboard de monitoramento
```

### Comparador de Fundos (Padrão)

Na primeira execução do comparador, ele irá:
- Baixar dados cadastrais e de políticas da CVM
- Criar banco de dados local (`output/fundos.db`)
- Exibir estatísticas e demonstração de comparação

### Dashboard de Monitoramento

Na primeira execução do dashboard, ele irá:
- Buscar todos os 22 datasets da CVM (aprox. 30 segundos)
- Criar um arquivo de estado (`cvm_state.json`)
- Exibir o dashboard completo
- Exportar dados para arquivos JSON e CSV
- Salvar uma versão em texto em `cvm_dashboard.txt`

### Execuções Subsequentes

Nas execuções seguintes, o script irá:
- Usar dados em cache para datasets não modificados (aprox. 2 segundos)
- Buscar apenas datasets modificados da API
- Mostrar o que mudou desde a última execução
- Atualizar todos os arquivos de exportação

## Arquivos Gerados

O script gera vários arquivos de saída:

| Arquivo | Descrição | Tamanho |
|---------|-----------|---------|
| `cvm_dashboard.txt` | Dashboard em texto puro (fácil de ler, sem cores) | ~5 KB |
| `cvm_state.json` | Arquivo de estado para rastreamento de mudanças | ~50 KB |
| `cvm_fundos_completo.json` | Catálogo completo com todos os metadados | ~74 KB |
| `cvm_fundos_recursos.csv` | Lista de recursos em formato CSV | ~29 KB |
| `cvm_metadata_summary.json` | Resumo do dashboard com estatísticas | ~9 KB |

### Para Usuários Windows

O arquivo texto (`cvm_dashboard.txt`) é especialmente útil para usuários Windows que preferem ler os resultados em um arquivo de texto simples ao invés do console. O arquivo contém as mesmas informações da saída do console, mas sem códigos de cor.

## Visão Geral dos Dados

O script monitora **22 datasets** em **7 tipos de fundos**:

### Tipos de Fundos

- **FI** - Fundos de Investimento (Fundos Gerais)
  - 10 datasets, 118 recursos
  - Informes diários, balancetes, informações cadastrais

- **FII** - Fundos de Investimento Imobiliário
  - 4 datasets, 24 recursos
  - Informes mensais, trimestrais e anuais

- **FIP** - Fundos de Investimento em Participações
  - 2 datasets, 7 recursos
  - Informes trimestrais e quadrimestrais

- **FIDC** - Fundos de Investimento em Direitos Creditórios
  - 1 dataset, 13 recursos
  - Informes mensais

- **FIAGRO** - Fundos de Investimento nas Cadeias Agroindustriais
  - 1 dataset, 6 recursos
  - Informes mensais

- **FIE** - Fundos de Investimento Estruturados
  - 3 datasets, 27 recursos
  - Balancetes e medidas mensais

- **OUTROS** - Outros datasets
  - 1 dataset, 6 recursos
  - Dados agregados de emissores

### Frequências de Atualização

- **Diária**: Informes diários de carteira dos fundos
- **Mensal**: Balancetes, perfis mensais, composição de carteira
- **Trimestral**: Informes trimestrais de FII e FIP
- **Anual**: Demonstrações financeiras anuais

## Recursos do Dashboard

### Estatísticas Resumidas
- Total de datasets e recursos
- Distribuição por tipo de fundo
- Distribuição por formato (ZIP, CSV, TXT, ODS)

### Detalhamento por Tipo de Fundo
- Organizado por categoria de fundo
- Timestamps das últimas atualizações
- Indicadores de frequência de atualização
- Cores indicando atualidade (verde = recente, amarelo = médio, vermelho = antigo)

### Detecção de Mudanças
O script rastreia automaticamente:
- ✅ Novos datasets
- ✅ Novos recursos (arquivos)
- ⚠️ Datasets modificados
- ⚠️ Recursos modificados
- ❌ Datasets removidos
- ❌ Recursos removidos

## Opções de Configuração

Você pode personalizar o comportamento do extrator:

```python
from script import CVMDataExtractor

# Criar extrator com opções customizadas
extractor = CVMDataExtractor(
    state_file='cvm_state.json',    # Caminho do arquivo de estado
    enable_colors=True,              # Ativar/desativar cores no terminal
    api_throttle=0.5,                # Delay entre chamadas à API (segundos)
    output_file='cvm_dashboard.txt'  # Caminho do arquivo texto de saída
)
```

### Desativar Saída em Arquivo Texto

Se você não quiser o arquivo texto:

```python
extractor = CVMDataExtractor(output_file=None)
```

### Desativar Cores (para problemas de compatibilidade no Windows)

```python
extractor = CVMDataExtractor(enable_colors=False)
```

## Exemplos

O script inclui várias funções de exemplo:

- `exemplo_basico()` - Uso básico com formato antigo de resumo
- `exemplo_busca()` - Buscar datasets específicos
- `exemplo_recursos_recentes()` - Listar arquivos CSV mais recentes
- `exemplo_exportacao()` - Exportar apenas metadados
- **`exemplo_dashboard()`** - Dashboard completo com rastreamento de mudanças (padrão)

Para executar um exemplo diferente, edite o bloco `if __name__ == "__main__"` no `script.py`.

## Performance

- **Primeira execução**: ~30 segundos (busca todos os 22 datasets)
- **Execuções subsequentes**: ~2 segundos (usa dados em cache)
- **Chamadas à API**: Cache inteligente reduz carga na API em 100% quando não há mudanças

## Solução de Problemas

### Problemas com Cores no Windows

Se você vê caracteres estranhos no console do Windows:
1. Use o Windows Terminal (recomendado) ou
2. Desative as cores: `CVMDataExtractor(enable_colors=False)` ou
3. Simplesmente leia o arquivo `cvm_dashboard.txt`

### ImportError: No module named 'ckanapi'

Certifique-se de que ativou o ambiente virtual e instalou as dependências:
```bash
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### Erros de Permissão no Windows

Execute seu terminal como Administrador se obtiver erros de permissão.

## Fonte dos Dados

Os dados são obtidos de:
- **Portal de Dados Abertos da CVM**: https://dados.cvm.gov.br
- **Grupo de Datasets**: fundos-de-investimento
- **Frequência de Atualização**: Diária (os datasets são atualizados pela CVM às 08:00 horário de Brasília)

## Licença

Este script é fornecido como está para acessar dados públicos da CVM. Os dados em si estão sujeitos à Licença de Dados Abertos da CVM (ODbL).

## Comparador de Fundos (Novo!)

O projeto agora inclui um sistema completo de comparação de fundos de investimento.

### Funcionalidades do Comparador

- **Download automático de dados**: Baixa dados cadastrais e de políticas da CVM
- **Banco de dados local**: Armazena dados em SQLite para consultas rápidas
- **Busca com filtros**: Filtre por situação, tipo, gestor, classe ANBIMA, patrimônio mínimo
- **Comparação lado a lado**: Compare múltiplos fundos por CNPJ
- **Rastreamento de mudanças**: Detecta alterações em taxas, gestores e situação
- **Exportação CSV**: Exporte comparações para análise externa

### Uso Rápido

```bash
# Executar comparador de fundos (padrão)
python main.py

# Carregar/atualizar dados da CVM
python main.py comparar --carregar

# Mostrar estatísticas dos fundos
python main.py comparar --stats

# Executar dashboard de monitoramento
python main.py dashboard

# Buscar datasets específicos (ex: FII)
python main.py dashboard --busca FII
```

### Uso Programático

```python
from src.analisador_fundos import AnalisadorFundos

analisador = AnalisadorFundos()

# Carregar dados da CVM (primeira vez)
analisador.carregar_dados()

# Buscar fundos ativos
fundos = analisador.banco.buscar_fundos({
    'situacao': 'EM FUNCIONAMENTO NORMAL',
    'tipo_fundo': 'FI'
})

# Comparar fundos por CNPJ
comparacao = analisador.comparar_fundos([
    '00.017.024/0001-53',
    '00.068.305/0001-35'
])

# Exportar para CSV
analisador.exportar_comparacao_csv(lista_cnpj, 'comparacao.csv')
```

### Estrutura de Diretórios

```
fundos-investimento/
├── main.py                     # Ponto de entrada unificado
├── src/                        # Módulos Python
│   ├── __init__.py             # Exportações do pacote
│   ├── analisador_fundos.py    # Comparador de fundos
│   ├── comparador_cli.py       # Interface de linha de comando
│   └── dashboard_cvm.py        # Dashboard de monitoramento
├── output/                     # Arquivos gerados
│   ├── fundos.db               # Banco de dados SQLite
│   ├── cache/                  # Cache de downloads
│   └── comparacao_*.csv        # Exportações
├── CLAUDE.md                   # Contexto do projeto para IA
└── README.md
```

## Contribuindo

Sinta-se à vontade para melhorar este script! Algumas ideias:
- Adicionar funcionalidade de download de arquivos ZIP
- Criar gráficos e visualizações
- Adicionar notificações por e-mail para mudanças
- Criar um dashboard web
- Adicionar suporte para outros grupos de dados da CVM
- Integrar dados de perfil mensal para análise de performance

## Suporte

Para questões relacionadas a:
- **Este script**: Verifique o código ou modifique conforme necessário
- **Dados da CVM**: Visite https://dados.cvm.gov.br
- **Python/dependências**: Consulte a documentação respectiva

---

**Última Atualização**: Janeiro de 2026
**Versão**: 3.0
**Autor**: Dashboard com comparador de fundos unificado
