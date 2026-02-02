# CVM Fundos de Investimento

Consolida dados de fundos de investimento brasileiros do Portal de Dados Abertos da CVM.

## Dados Atualizados

📊 **Acesse os dados atualizados diariamente:**

https://drive.google.com/drive/u/0/folders/1IdD1fcA2Ou79frCGepjH9CqMveQBP41m

> Os arquivos são atualizados automaticamente todo dia às 08:30h (horário de Brasília).

## Arquivos Disponíveis

| Arquivo | Conteúdo |
|---------|----------|
| **fundos.csv** | Cadastro de fundos ativos (~33k fundos) |
| **composicao_carteira.csv** | Composição da carteira (~350k posições) |

Os dois arquivos se relacionam pelo **CNPJ**.

### fundos.csv

```
cnpj, nome_fundo, tipo_fundo, gestor, administrador,
custodiante, patrimonio_liquido, classificacao_anbima, publico_alvo
```

### composicao_carteira.csv

```
cnpj, tipo_aplicacao, tipo_ativo, descricao_ativo,
emissor, valor_mercado, quantidade, data_competencia
```

## Fonte dos Dados

- **Cadastro**: `registro_fundo_classe.zip` (Resolução CVM 175)
- **Carteira**: `cda_fi_YYYYMM.zip` (Composição e Diversificação)
- **Portal**: https://dados.cvm.gov.br

---

## Uso Local

### Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Comandos

```bash
python main.py                      # Consolida dados (usa cache)
python main.py consolidate --force  # Força re-download
python main.py auth                 # Autenticar com Google Drive
python main.py upload               # Upload para Google Drive
```

> **Nota**: Para dados atualizados, use `--force`. A CVM atualiza o cadastro diariamente às 08:00h.
> A composição da carteira (CDA) é atualizada mensalmente com defasagem de ~2 meses.
