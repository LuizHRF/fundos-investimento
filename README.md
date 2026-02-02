# CVM Fundos de Investimento

Consolida dados de fundos de investimento brasileiros do Portal de Dados Abertos da CVM.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python main.py                      # Consolida dados (usa cache)
python main.py consolidate --force  # Força re-download
```

> **Nota**: Para dados atualizados, use `--force`. A CVM atualiza diariamente às 08:00h.

## Arquivos de Saída

| Arquivo | Conteúdo |
|---------|----------|
| **fundos.csv** | Cadastro de fundos ativos (uma linha por fundo) |
| **composicao_carteira.csv** | Composição da carteira (múltiplas linhas por fundo) |

Os dois arquivos se relacionam pelo **CNPJ**.

### fundos.csv (~33k fundos ativos)

```
cnpj, nome_fundo, tipo_fundo, gestor, administrador,
custodiante, patrimonio_liquido, classificacao_anbima, publico_alvo
```

### composicao_carteira.csv (~350k posições)

```
cnpj, tipo_aplicacao, tipo_ativo, descricao_ativo,
emissor, valor_mercado, quantidade, data_competencia
```

## Fonte dos Dados

- **Cadastro**: `registro_fundo_classe.zip` (Resolução CVM 175)
- **Carteira**: `cda_fi_YYYYMM.zip` (Composição e Diversificação)
- **Portal**: https://dados.cvm.gov.br
