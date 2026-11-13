# Ambiente: SGBD e dataset

## SGBD (restrição do PDF: comercial, não MySQL)
| SGBD | Edição gratuita | Plano de execução |
|---|---|---|
| **SQL Server** | Developer (uso não produtivo) / Express (limite de 10 GB por banco) | Gráfico no SSMS, `STATISTICS IO/TIME` |
| Oracle | Database Free (antigo XE) | `EXPLAIN PLAN`, `DBMS_XPLAN`, AUTOTRACE |
| IBM Db2 | Community Edition | `EXPLAIN`, `db2exfmt` |

PostgreSQL é open source e NoSQL não atende ao requisito. Não use.

**Recomendação:** SQL Server Developer (Windows, plano gráfico). Alternativa: Oracle Free. Registre a escolha em [decisões e riscos](../09-decisoes-e-pendencias/decisoes-e-riscos.md).

## Dataset (decisão pendente)
Critérios: ≥ 1 milhão de linhas (ideal 5–10 M), várias tabelas relacionadas, colunas variadas, licença aberta, cabe na edição escolhida.

| Opção | Observação |
|---|---|
| Dados sintéticos por script | Controle total, reprodutível. Plano B seguro |
| Stack Overflow data dump | Grande e relacional (dump público; conferir licença) |
| NYC TLC Trip Records | Muitos milhões de linhas, tabela única |
| Dados abertos BR (CNPJ da Receita, microdados do ENEM/INEP) | Grandes e relevantes localmente |
| AdventureWorks / WideWorldImporters / ContosoRetailDW | Exemplos da Microsoft, pequenos (precisam ser ampliados) |
| Olist (Kaggle) | Relacional, apenas ~100 mil pedidos: pequeno demais |

Documentar: fonte (URL), licença, tamanho, esquema e forma de carga.
