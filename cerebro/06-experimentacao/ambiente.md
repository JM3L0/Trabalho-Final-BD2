# Ambiente: SGBD, Infraestrutura Local e Dataset

## SGBD Definido (restrição do PDF: comercial, não MySQL)
- **Escolha:** **Microsoft SQL Server 2022 Developer Edition** em container Docker (`mcr.microsoft.com/mssql/server:2022-latest`, `MSSQL_PID=Developer`).
- **Justificativa:** Ver [comparativo-sgbds.md](../../comparativo-sgbds.md). É inequivocamente comercial, gratuito para uso não produtivo, sem limite de 10 GB por banco (ao contrário do Express), possui plano gráfico no SSMS/VS Code (`mssql`) e métricas exatas via `SET STATISTICS IO, TIME ON` e `SET STATISTICS XML ON`.
- **Registro da decisão:** [decisoes-e-riscos.md](../09-decisoes-e-pendencias/decisoes-e-riscos.md).

## Máquina de Experimentos (verificada em 13/11/2026)
- **SO:** Microsoft Windows 11 Home Single Language
- **CPU:** 12th Gen Intel(R) Core(TM) i5-1235U (10 núcleos / 12 threads)
- **RAM:** 15,71 GB (~16 GB)
- **Armazenamento:** SSD (`KINGSTON SA400S37240G` 224 GB e `SAMSUNG MZVLQ256HBJD-00B` 238 GB)
- **Ferramentas instaladas no host:**
  - **Docker Desktop:** instalado (`docker.exe` disponível; **necessário iniciar o Docker Desktop** para ativar o daemon Linux).
  - **Python + `uv`:** instalados (para geração/carga de dados, automação das repetições e análise estatística).
  - **MiKTeX (`pdflatex`):** instalado (para compilar o paper em LaTeX).
  - **`sqlcmd`:** não instalado no host Windows; usar `/opt/mssql-tools18/bin/sqlcmd` dentro do container ou driver Python.

## Primeiros Passos do Setup
1. Abrir o **Docker Desktop** no Windows e aguardar o motor iniciar.
2. Criar `docker-compose.yml` com `mcr.microsoft.com/mssql/server:2022-latest`, `ACCEPT_EULA=Y`, `MSSQL_PID=Developer`, memória alocada compatível com os 15,71 GB do host e volume persistente para `/var/opt/mssql`.
3. Subir o container (`docker compose up -d`) e confirmar versão exata com `SELECT @@VERSION;`.
4. Configurar cliente gráfico para capturar planos de execução visuais: extensão **`SQL Server (mssql)`** no VS Code (mais leve) ou **SSMS** (SQL Server Management Studio).

## Dataset (decisão pendente)
Critérios: ≥ 1 milhão de linhas (ideal 5–10 M), várias tabelas relacionadas, colunas variadas, licença aberta, cabe em disco e na RAM disponível.

| Opção | Observação |
|---|---|
| **Dados sintéticos por script (Recomendado pelo prazo)** | Ex.: esquema relacional de e-commerce (`Clientes`, `Produtos`, `Pedidos` ~2M linhas, `ItensPedido` ~6M linhas) carregado via `bcp`/`BULK INSERT`. Controle total de seletividade/cardinalidade e 100% reprodutível |
| Stack Overflow data dump | Grande e relacional (dump público; conferir licença e tempo de download/carga) |
| NYC TLC Trip Records | Muitos milhões de linhas, tabela única (menos rico para `JOIN`) |
| Dados abertos BR (CNPJ da Receita, microdados do ENEM/INEP) | Grandes e relevantes localmente, porém exigem ETL mais demorado |
| AdventureWorks / WideWorldImporters / ContosoRetailDW | Exemplos da Microsoft, pequenos (precisam ser ampliados) |
| Olist (Kaggle) | Relacional, apenas ~100 mil pedidos: pequeno demais |

Documentar ao escolher: fonte (URL) ou script gerador, licença, linhas por tabela, tamanho em disco, esquema DDL e forma de carga.
