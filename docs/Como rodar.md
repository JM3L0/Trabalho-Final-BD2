## 1. Visao Geral da Arquitetura

O projeto adota uma metodologia cientifica rigorosa baseada em **duas bases gemeas na mesma instancia**:

1. **`Ecommerce_Baseline` (Grupo de Controle):** Contem o esquema relacional E-Commerce B2C com 6.250.000 registros povoado apenas com as 4 chaves primarias clusterizadas (`PK`), sem nenhum indice secundario.
2. **`Ecommerce_Otimizado` (Grupo Experimental):** Clonada diretamente da baseline via `BACKUP DATABASE` e `RESTORE DATABASE ... WITH MOVE`, recebendo **9 indices secundarios estrategicos** (indices B+ Tree simples, compostos ordenados, de cobertura com clausula `INCLUDE` e filtrados com `WHERE`).

Essa abordagem assegura identidade binaria exata de tuplas e estatisticas no instante inicial e viabiliza a demonstracao ao vivo sem a necessidade de criar ou remover indices durante a apresentacao.

---

## 2. Requisitos de Ambiente

O projeto foi projetado para funcionar com paridade total tanto no **Microsoft Windows** (10/11) quanto no **Ubuntu Linux** (20.04/22.04/24.04).

* **Docker:** Docker Desktop (Windows) ou Docker Engine (Ubuntu).
* **Python e uv:** Python 3.10+ e gerenciador de dependencias `uv` (Astral).
* **Compilador LaTeX:** TeX Live (Ubuntu: `sudo apt install texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-lang-portuguese`) ou MiKTeX / TeX Live (Windows).
* **Cliente SQL para Planos Graficos:** Visual Studio Code com a extensao oficial **`SQL Server (mssql)`** (`ms-mssql.mssql`) ou Azure Data Studio.

---

## 3. Passo a Passo de Instalacao e Execucao

### Passo 0: Clonar o Repositorio e Sincronizar Dependencias Python

```bash
# Clone ou acesse o diretorio raiz do projeto
cd Trabalho-Final-BD2

# Instalar o uv (caso ainda nao possua)
# No Ubuntu Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# No Windows PowerShell:
# powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Sincronizar dependencias do projeto (pymssql, numpy, scipy, matplotlib)
uv sync
```

---

### Passo 1: Subir o Container do SQL Server 2022 Developer

No Ubuntu Linux, ajuste primeiro as permissoes da pasta de dados para o usuario do container (`uid 10001`):

```bash
# No Ubuntu Linux:
bash scripts/setup_ubuntu.sh
# (ou manualmente: mkdir -p ./data && chmod -R 777 ./data)
```

Suba o container com espera automatica do teste de saude (`healthcheck`):

```bash
docker compose up -d --wait
```

---

### Passo 2: Teste de Fumaca e Conectividade (Smoke Test)

Valide a conexao com o banco, versao do SQL Server, limites de memoria e ativacao de metricas de I/O e planos XML:

```bash
uv run python scripts/smoke_test.py
```

*Saida esperada:* Exibicao da versao `Microsoft SQL Server 2022`, confirmacao do driver `pymssql` e resolucao de metricas de `STATISTICS IO` e `STATISTICS XML`.

---

### Passo 3: Geracao do Dataset Sintetico (6.250.000 Registros)

Gera os 4 arquivos CSV com semente pseudoaleatoria fixa (`seed=42`) para garantir 100% de reprodutibilidade:

```bash
uv run python scripts/generate_data.py
```

*Tabelas geradas na pasta `./data`:*
* `clientes.csv`: 200.000 registros (~16 MB)
* `produtos.csv`: 50.000 registros (~3 MB)
* `pedidos.csv`: 1.500.000 registros (~73 MB)
* `itens_pedido.csv`: 4.500.000 registros (~154 MB)
* **Total:** 6.250.000 tuplas (~245 MB em disco).

---

### Passo 4: Criacao da Base e Esquema Relacional Inicial

Executa o script DDL ([scripts/sql/01_create_baseline_db.sql](scripts/sql/01_create_baseline_db.sql)) criando o banco `Ecommerce_Baseline`, suas 4 tabelas e respectivas chaves primarias e estrangeiras:

```bash
uv run python scripts/create_schema.py
```

*Saida esperada:* Confirmacao das tabelas criadas com suas chaves primarias clusterizadas e integridade referencial ativa.

---

### Passo 5: Carga Massiva via BULK INSERT

Executa a carga em lotes ([scripts/sql/02_bulk_load_baseline.sql](scripts/sql/02_bulk_load_baseline.sql)) sob modelo `RECOVERY SIMPLE` e `BATCHSIZE = 100000`, preservando acentos em UTF-16 e validando contagens exatas e chaves estrangeiras:

```bash
uv run python scripts/load_baseline.py
```

*Saida esperada:*
* Clientes: 200.000
* Produtos: 50.000
* Pedidos: 1.500.000
* ItensPedido: 4.500.000
* Verificacao de integridade referencial: 0 violacoes de FKs (`is_not_trusted = 0`).

---

### Passo 6: Clonagem da Base Gemea Otimizada

Gera um backup completo da baseline (`ecommerce_init.bak`) e restaura com a clausula `WITH MOVE` para criar a base `Ecommerce_Otimizado` com dados binariamente identicos:

```bash
uv run python scripts/clone_optimized.py
```

*Saida esperada:* Confirmacao da clonagem e validacao de contagens identicas entre `Ecommerce_Baseline` e `Ecommerce_Otimizado`.

---

### Passo 7: Aplicacao dos 9 Indices Secundarios na Base Otimizada

Executa o script DDL ([scripts/sql/04_create_indexes_optimized.sql](scripts/sql/04_create_indexes_optimized.sql)) implantando exclusivamente em `Ecommerce_Otimizado` os indices secundarios simples, compostos, cobridores (`INCLUDE`) e filtrados:

```bash
uv run python scripts/apply_optimizations.py
```

*Indices criados:*
1. `IX_Clientes_Email` em `Clientes (Email)`
2. `IX_Produtos_Nome` em `Produtos (Nome)` com `INCLUDE (Categoria, Preco)`
3. `IX_Pedidos_DataPedido` em `Pedidos (DataPedido)` com `INCLUDE (ClienteID, Status, ValorTotal)`
4. `IX_Pedidos_Status_Data` composto em `Pedidos (Status, DataPedido)`
5. `IX_Pedidos_ClienteID_Cov` em `Pedidos (ClienteID)` com `INCLUDE (DataPedido, ValorTotal)`
6. `IX_Pedidos_Status_Cov` em `Pedidos (Status)` com `INCLUDE (ValorTotal)`
7. `IX_ItensPedido_PedidoID` em `ItensPedido (PedidoID)` com `INCLUDE (ProdutoID, Quantidade, PrecoUnitario)`
8. `IX_ItensPedido_ProdutoID` em `ItensPedido (ProdutoID)`
9. `IX_ItensPedido_Desconto_Alto` filtrado em `ItensPedido (ProdutoID, Desconto)` com `WHERE Desconto >= 10.00`

---

### Passo 8: Execucao da Bateria de Benchmarks Estatisticos

Dispara a suíte automatizada de testes cobrindo as 10 consultas de leitura ($Q_1$ a $Q_{10}$) e 1 carga de escrita massiva ($W_1$) com `OPTION (MAXDOP 1)`:

```bash
uv run python scripts/run_benchmarks.py
```

* **Warm Cache:** $N = 30$ repeticoes consecutivas por cenario (descartando o aquecimento inicial).
* **Cold Cache:** $N = 10$ repeticoes com sanitizacao de memoria e planos (`CHECKPOINT; DBCC DROPCLEANBUFFERS; DBCC FREEPROCCACHE;`).
* **Seguranca em W1:** As insercoes em lote de 10.000 tuplas sao executadas sob `BEGIN TRANSACTION ... ROLLBACK TRANSACTION`, mantendo a cardinalidade intacta em exatos 4.500.000 registros ao final.
* **Artefatos gerados:** Salva os planos reais `.sqlplan` em `results/plans/` e as metricas brutas em `results/benchmark_runs.csv`.

---

### Passo 9: Consolidacao Estatistica e Geracao de Graficos

Processa as amostras brutas, calcula medias, medianas, desvios padrao, intervalos de confianca de 95%, speedups, testes de normalidade (Shapiro-Wilk) e testes de hipotese (Teste t pareado / Wilcoxon com p-valor):

```bash
# Consolida a tabela resumo em CSV e a tabela formatada em LaTeX
uv run python scripts/analyze_results.py

# Gera as figuras comparativas de alta resolucao (300 DPI) para o paper
uv run python scripts/generate_charts.py

# Gera os diagramas das arvores de operadores de execucao
uv run python scripts/generate_plan_diagrams.py
```

*Artefatos gerados:*
* `results/summary_table.csv` e `results/summary_stats.json`: Tabela consolidada com todas as metricas.
* `paper/generated/tabela_resultados.tex`: Tabela em formato booktabs pronta para o artigo.
* `paper/figures/`: Boxplots de tempo, reducao percentual de leituras logicas, comparativo warm vs cold, estagios de Key Lookup e arvores de operadores.

---

### Passo 10: Validacao Automatizada do Kit de Demonstracao ao Vivo

Valida se todos os 4 scripts SQL de demonstracao da apresentacao oral executam perfeitamente no container:

```bash
uv run python scripts/test_demo_kit.py
```

*Saida esperada:* `[OK] Todos os scripts de demonstracao foram validados com sucesso!`

---

### Passo 11: Compilacao do Artigo Cientifico em LaTeX (Padrao SBC)

Compila o paper com `pdflatex` e `bibtex`, validando automaticamente se o documento atende ao limite maximo de 10 paginas do edital:

```bash
uv run python scripts/compile_paper.py
```

*Saida gerada:*
* [paper/main.pdf](paper/main.pdf) (10 paginas exatas, sem advertencias de margem *Overfull \hbox*).

---

## 4. Guia da Demonstracao Pratica ao Vivo (Apresentacao de 20 Minutos)

Durante a apresentacao oral (Slide 12 / Pagina 12 de `slides/apresentacao.pdf`), a equipe dispoe de **4 a 5 minutos** para demonstrar o contraste ao vivo entre as duas bases:

### Como Executar no VS Code (`ms-mssql.mssql`):
1. Abra o VS Code com a extensao **`SQL Server (mssql)`** conectada a `localhost,1433` (usuario `sa`, senha `Bd2Trabalho!2026`).
2. Abra os 4 scripts da pasta [scripts/demo/](scripts/demo/):
   * `01_q1_seek_vs_scan.sql`: Mostra a busca pontual por e-mail saindo de *Clustered Index Scan* (2.856 leituras) para *Index Seek* (6 leituras, $<1$ ms).
   * `02_q3_indice_composto.sql`: Mostra o ganho da ordem de chaves `(Status, DataPedido)` saindo de 8.090 leituras para 17 leituras (speedup de 87x).
   * `03_q4_eliminacao_key_lookup.sql`: Mostra a eliminacao completa do *Key Lookup* com o indice cobridor `INCLUDE (DataPedido, ValorTotal)` (de 8.090 leituras para 5 leituras).
   * `04_w1_tradeoff_escrita.sql`: Mostra a amplificacao de escrita DML em 4 arvores B+ simultaneas (+85,33% de I/O) com `ROLLBACK` automatico.
3. Ative **Enable Actual Plan** (`Ctrl+M` ou icone de grafico na barra superior).
4. Execute o script (`Ctrl+Shift+E`): o resultado e os dois planos de execucao aparecem lado a lado instantaneamente, sem travar e sem rodar nenhum comando DDL.

### Planos de Contingencia:
* **Plano B (Container indisponivel):** Abrir diretamente no VS Code os arquivos de plano pre-capturados em `results/plans/` (`.sqlplan`).
* **Plano C (Falha eletrica/projetor):** Video demonstrativo de backup gravado em tela cheia da execucao dos 4 scripts.

---

## 5. Como Interpretar as Metricas e Operadores

### Metricas Principais:
* **Leituras Logicas (`logical reads`):** O numero de paginas de 8 KB acessadas na memoria (*buffer pool*). E a metrica mais fidedigna e deterministica de desempenho em banco de dados, pois independe de interferencias transitórias de carga no processador.
* **Tempo Decorrido (*Elapsed Time*) e CPU:** Medem a latencia percebida pela aplicacao e o custo em ciclos de processamento.
* **Speedup:** Fator de aceleracao calculado por $\frac{Tempo_{Baseline}}{Tempo_{Otimizado}}$.
* **Valor-p (*p-value*):** Calculado via Teste t de Student pareado ou Teste de postos com sinais de Wilcoxon. Valores $p < 0,001$ atestam significancia estatistica formal com $N=30$.

### Operadores Fisicos no Plano de Execucao:
* **Clustered Index Scan / Table Scan:** Varredura completa da tabela ($O(N)$). Ocorre no Baseline quando nao ha caminho de acesso seletivo.
* **Index Seek:** Busca binaria eficiente navegando na arvore B+ do no raiz as folhas ($O(\log_m N)$).
* **Key Lookup (Bookmark Lookup):** Busca de colunas faltantes na tabela principal quando o indice secundario nao e de cobertura.
* **Covering Index (`INCLUDE`):** Armazena as colunas projetadas no nivel folha do indice, eliminando integralmente os Key Lookups.
* **Sort:** Operador custoso de ordenacao em memoria/TempDB. E eliminado quando a consulta se apoia em um indice cuja chave ja esta ordenada na direcao do `ORDER BY`.
* **Hash Match vs. Merge / Nested Loops:** Em juncoes ($Q_5$), a presenca de indices nas chaves estrangeiras permite substituir o custoso *Hash Match* por *Merge Join* e *Nested Loops*.

### Trade-offs Essenciais a Destacar na Apresentacao:
1. **O Mito do Indice Gratuito ($W_1$):** Indices secundarios aceleram leituras de 10x a 400x, mas penalizam insercoes em lote (+85,33% de I/O em $W_1$) devido a manutencao sincrona de multiplas arvores B+.
2. **Inversao de Latencia em $Q_7$ (Batch Mode vs. Row Mode):** Em $Q_7$, o indice reduziu as leituras logicas em 30,06%, mas o tempo subiu ligeiramente (de 217 ms para 364 ms) porque o SQL Server 2022 executou o *Hash Match* original em **Batch Mode on Rowstore** (vetorizado com ~900 linhas por pacote), enquanto o indice forcou um *Stream Aggregate* em **Row Mode** (linha a linha). Essa analise evidencia dominio tecnico profundo da engine.

---

## 6. Estrutura de Diretorios

```text
Trabalho-Final-BD2/
├── README.md                      # Este guia completo de execucao e interpretacao
├── docker-compose.yml             # Definicao do container SQL Server 2022 Developer
├── pyproject.toml / uv.lock       # Dependencias e ambiente Python gerenciado por uv
├── .env.example                   # Variaveis de ambiente para porta e senha SA
├── data/                          # Diretorio montado no container para os CSVs gerados
├── scripts/
│   ├── smoke_test.py              # Teste inicial de conectividade e versoes
│   ├── generate_data.py           # Gerador reprodutivel do dataset (seed=42)
│   ├── create_schema.py           # DDL de criacao da base e tabelas iniciais
│   ├── load_baseline.py           # Carga massiva via BULK INSERT em lotes
│   ├── clone_optimized.py         # Clonagem da base gemea via Backup/Restore
│   ├── apply_optimizations.py     # DDL dos 9 indices secundarios na base otimizada
│   ├── run_benchmarks.py          # Benchmark automatizado (N=30 Warm, N=10 Cold, MAXDOP 1)
│   ├── analyze_results.py         # Consolidacao estatistica e testes de hipotese
│   ├── generate_charts.py         # Gerador de graficos em alta resolucao (300 DPI)
│   ├── generate_plan_diagrams.py  # Diagramacao visual dos planos de execucao
│   ├── compile_paper.py           # Compilador e validador do artigo SBC (<= 10 pags)
│   ├── test_demo_kit.py           # Teste automatizado dos scripts da demonstracao
│   ├── sql/                       # Scripts Transact-SQL de DDL e carga
│   └── demo/                      # Scripts SQL numerados (01 a 04) para a demo ao vivo
├── paper/
│   ├── main.tex                   # Artigo cientifico completo no padrao SBC
│   ├── main.pdf                   # PDF compilado do artigo (exatas 10 paginas)
│   ├── sbc.bst / sbc-template.sty # Arquivos de estilo oficial da SBC
│   └── figures/                   # Figuras e graficos em PNG de alta resolucao
├── results/
│   ├── summary_table.csv          # Tabela com medias, medianas, speedups e p-valores
│   ├── summary_stats.json         # Estatisticas completas em JSON
│   └── plans/                     # Planos reais salvos em formato .sqlplan (XML)
├── slides/
│   ├── apresentacao.tex           # Slides da apresentacao em LaTeX Beamer (16:9)
│   ├── apresentacao.pdf           # Slides compilados em PDF (13 slides)
│   └── roteiro-apresentacao.md    # Roteiro de fala cronometrado (17m30s)
└── cerebro/                       # Base de conhecimento e documentacao detalhada
```
