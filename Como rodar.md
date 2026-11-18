
---

## 1. Visão Geral da Arquitetura

O projeto adota uma metodologia científica rigorosa baseada em **duas bases gêmeas na mesma instância** do SQL Server 2022:

1. **`Ecommerce_Baseline` (Grupo de Controle):** Contém o esquema relacional E-Commerce B2C com **6.250.000 registros** povoado apenas com as 4 chaves primárias clusterizadas (`PK`), sem nenhum índice secundário.
2. **`Ecommerce_Otimizado` (Grupo Experimental):** Clonada diretamente da baseline via `BACKUP DATABASE` e `RESTORE DATABASE ... WITH MOVE`, recebendo **9 índices secundários estratégicos** (árvores B+ simples, compostos ordenados, índices de cobertura com cláusula `INCLUDE` e índices filtrados com predicado `WHERE`).

Essa abordagem assegura identidade binária exata de tuplas e estatísticas no instante inicial e viabiliza a demonstração ao vivo durante a apresentação sem a necessidade de criar ou remover índices em tempo real.

---

## 2. Requisitos de Ambiente no Windows

Para rodar todo o pipeline no Windows, você precisará das seguintes ferramentas:

1. **Docker Desktop para Windows:**
   - Com backend WSL 2 ativado (recomendado) ou Hyper-V.
   - Certifique-se de que o Docker Desktop está aberto e rodando (ícone da baleia verde na bandeja do sistema).
   - *Recursos recomendados:* Pelo menos 4 GB de memória RAM disponíveis para os containers.
2. **Python 3.10+ Nativo com `venv`:**
   - Python instalado no Windows (3.10, 3.11, 3.12 ou 3.13) com a opção "Add python.exe to PATH" marcada no instalador.
   - O ambiente isolado do projeto será criado diretamente via módulo nativo `venv`.
3. **Cliente SQL para Visualização dos Planos Gráficos de Execução:**
   - **Visual Studio Code** com a extensão oficial **`SQL Server (mssql)`** (`ms-mssql.mssql`) — *Recomendado*.
   - Ou **SQL Server Management Studio (SSMS)** / **Azure Data Studio**.
4. **Compilador LaTeX (Opcional):**
   - Necessário **apenas** se você desejar recompilar o artigo científico ([paper/main.tex](file:///c:/Users/raild/Downloads/Trabalho-Final-BD2/paper/main.tex)) ou os slides ([slides/apresentacao.tex](file:///c:/Users/raild/Downloads/Trabalho-Final-BD2/slides/apresentacao.tex)).
   - No Windows: **MiKTeX** (`winget install MiKTeX.MiKTeX`) ou **TeX Live**.
   - *Nota:* O PDF final do artigo ([paper/main.pdf](file:///c:/Users/raild/Downloads/Trabalho-Final-BD2/paper/main.pdf)) e dos slides já estão pré-compilados e inclusos no repositório.

---

## 3. Passo a Passo de Instalação e Execução no Windows (PowerShell)

Abra o **PowerShell** no diretório raiz do projeto:

```powershell
cd c:\Users\raild\Downloads\Trabalho-Final-BD2
```

> [!TIP]
> Se for a primeira vez que você ativa um ambiente virtual no PowerShell e o Windows exibir um aviso de política de execução restrita, execute uma única vez:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

---

### Passo 0: Criar e Ativar o Ambiente Virtual (`venv`)

Crie o ambiente virtual com o Python nativo e instale as dependências necessárias:

```powershell
# 1. Cria a pasta do ambiente virtual .venv
python -m venv .venv

# 2. Ativa o ambiente virtual no PowerShell
.\.venv\Scripts\Activate.ps1

# 3. Atualiza o pip e instala as dependências do projeto
python -m pip install --upgrade pip
pip install matplotlib numpy pymssql python-dotenv scipy
```

> [!NOTE]
> Quando o ambiente virtual está ativo, o prompt do PowerShell exibirá o prefixo `(.venv)`.  
> A partir daqui, todos os comandos `python` utilizarão as bibliotecas deste ambiente isolado.

---

### Passo 1: Subir o Container do SQL Server 2022 Developer

O arquivo [docker-compose.yml](file:///c:/Users/raild/Downloads/Trabalho-Final-BD2/docker-compose.yml) configura o Microsoft SQL Server 2022 Developer com limite de memória de 4 GB (`mem_limit: 4g`), porta `1433` e montagem do diretório `./data` em `/var/opt/mssql/data_import`.

Suba o container com espera automática pelo *healthcheck*:

```powershell
docker compose up -d --wait
```

> [!NOTE]
> No Windows com Docker Desktop, o compartilhamento da pasta `./data` é automático. Diferente do Linux, **não** é necessário executar scripts de permissão (`chmod` ou `setup_ubuntu.sh`).

---

### Passo 2: Teste de Fumaça e Conectividade (Smoke Test)

Valide a conexão com o banco de dados, versão do SQL Server 2022, driver `pymssql` e a captura de estatísticas de I/O e planos XML:

```powershell
python scripts/smoke_test.py
```

*Saída esperada:* Exibição da versão `Microsoft SQL Server 2022`, confirmação do driver e sucesso no parsing de métricas de `STATISTICS IO` e `STATISTICS XML`.

---

### Passo 3: Geração do Dataset Sintético (6.250.000 Registros)

Gera os 4 arquivos CSV na pasta `./data/` com semente pseudoaleatória fixa (`seed=42`) para garantir 100% de reprodutibilidade científica:

```powershell
python scripts/generate_data.py
```

*Tabelas geradas na pasta `./data`:*
* `clientes.csv`: 200.000 registros (~16 MB)
* `produtos.csv`: 50.000 registros (~3 MB)
* `pedidos.csv`: 1.500.000 registros (~73 MB)
* `itens_pedido.csv`: 4.500.000 registros (~154 MB)
* **Total:** 6.250.000 tuplas (~245 MB em disco).

---

### Passo 4: Criação da Base e Esquema Relacional Inicial

Executa o script DDL ([scripts/sql/01_create_baseline_db.sql](file:///c:/Users/raild/Downloads/Trabalho-Final-BD2/scripts/sql/01_create_baseline_db.sql)) criando a base `Ecommerce_Baseline`, suas 4 tabelas relacionais e as chaves primárias e estrangeiras:

```powershell
python scripts/create_schema.py
```

*Saída esperada:* Confirmação da criação do banco `Ecommerce_Baseline` com chaves primárias clusterizadas e integridade referencial ativa.

---

### Passo 5: Carga Massiva via BULK INSERT

Executa a carga em lotes ([scripts/sql/02_bulk_load_baseline.sql](file:///c:/Users/raild/Downloads/Trabalho-Final-BD2/scripts/sql/02_bulk_load_baseline.sql)) sob modelo `RECOVERY SIMPLE` e `BATCHSIZE = 100000`, preservando caracteres especiais em UTF-16 e validando contagens exatas e integridade de chaves estrangeiras:

```powershell
python scripts/load_baseline.py
```

*Saída esperada:*
* Clientes: 200.000
* Produtos: 50.000
* Pedidos: 1.500.000
* ItensPedido: 4.500.000
* Integridade referencial: 0 violações de FKs (`is_not_trusted = 0`).

---

### Passo 6: Clonagem da Base Gêmea Otimizada

> [!IMPORTANT]
> **Este passo é obrigatório antes do Passo 7!**  
> Ele gera um backup completo da baseline (`ecommerce_init.bak`) e restaura com a cláusula `WITH MOVE` para criar a base `Ecommerce_Otimizado` com dados binariamente idênticos.  
> Se você tentar rodar o Passo 7 sem ter executado este passo, o SQL Server retornará o erro `Login failed for user 'sa' (18456)` porque o banco `Ecommerce_Otimizado` ainda não existirá.

Execute a clonagem:

```powershell
python scripts/clone_optimized.py
```

*Saída esperada:* Confirmação da clonagem e validação de contagens idênticas entre `Ecommerce_Baseline` e `Ecommerce_Otimizado`.

---

### Passo 7: Aplicação dos 9 Índices Secundários na Base Otimizada

Executa o script DDL ([scripts/sql/04_create_indexes_optimized.sql](file:///c:/Users/raild/Downloads/Trabalho-Final-BD2/scripts/sql/04_create_indexes_optimized.sql)) implantando exclusivamente em `Ecommerce_Otimizado` os 9 índices secundários estratégicos:

```powershell
python scripts/apply_optimizations.py
```

*Índices implantados:*
1. `IX_Clientes_Email` em `Clientes (Email)` — Busca pontual.
2. `IX_Produtos_Nome` em `Produtos (Nome)` com `INCLUDE (Categoria, Preco)` — Busca prefixada sem Key Lookup.
3. `IX_Pedidos_DataPedido` em `Pedidos (DataPedido)` com `INCLUDE (ClienteID, Status, ValorTotal)` — Range semiaberto cobridor.
4. `IX_Pedidos_Status_Data` composto em `Pedidos (Status, DataPedido)` — Igualdade + ordenação.
5. `IX_Pedidos_ClienteID_Cov` em `Pedidos (ClienteID)` com `INCLUDE (DataPedido, ValorTotal)` — Agregação por cliente sem Key Lookup.
6. `IX_Pedidos_Status_Cov` em `Pedidos (Status)` com `INCLUDE (ValorTotal)` — Agregação por status.
7. `IX_ItensPedido_PedidoID` em `ItensPedido (PedidoID)` com `INCLUDE (ProdutoID, Quantidade, PrecoUnitario)` — Junção cobridora.
8. `IX_ItensPedido_ProdutoID` em `ItensPedido (ProdutoID)` — Suporte à FK para agregação.
9. `IX_ItensPedido_Desconto_Alto` filtrado em `ItensPedido (ProdutoID, Desconto)` com `WHERE Desconto >= 10.00` — Índice compacto de 901.180 linhas.

---

### Passo 8: Execução da Bateria de Benchmarks Estatísticos

Dispara a suíte automatizada de testes cobrindo as 10 consultas de leitura ($Q_1$ a $Q_{10}$) e a carga de escrita massiva ($W_1$) com `OPTION (MAXDOP 1)`:

```powershell
python scripts/run_benchmarks.py
```

* **Warm Cache:** $N = 30$ repetições consecutivas por cenário (descartando as 2 rodadas iniciais de aquecimento).
* **Cold Cache:** $N = 10$ repetições com sanitização de memória RAM e planos de execução (`CHECKPOINT; DBCC DROPCLEANBUFFERS; DBCC FREEPROCCACHE;`).
* **Segurança em $W_1$:** As inserções em lote de 10.000 tuplas são executadas sob `BEGIN TRANSACTION ... ROLLBACK TRANSACTION`, mantendo a cardinalidade intacta em exatos 4.500.000 registros ao final.
* **Artefatos gerados:** Planos de execução reais `.sqlplan` em `results/plans/` e métricas brutas em `results/benchmark_runs.csv`.

---

### Passo 9: Análise Estatística e Geração de Gráficos

Consolida as métricas, calcula médias, medianas, desvios padrão, intervalos de confiança de 95%, speedups, testes de normalidade (Shapiro-Wilk) e testes de hipótese pareados (Teste *t* ou Wilcoxon):

```powershell
# Consolida a tabela resumo em CSV e JSON
python scripts/analyze_results.py

# Gera os gráficos comparativos em alta resolução (300 DPI) para o artigo
python scripts/generate_charts.py

# Gera os diagramas das árvores de operadores físicos de execução
python scripts/generate_plan_diagrams.py
```

*Artefatos gerados:*
* `results/summary_table.csv` e `results/summary_stats.json`: Estatísticas consolidadas.
* `paper/figures/`: Boxplots de tempo, redução percentual de leituras lógicas, comparativo warm vs cold, estágios de Key Lookup e árvores de operadores.

---

### Passo 10: Validação Automatizada do Kit de Demonstração

Valida se todos os 4 scripts SQL da demonstração prática da apresentação oral executam com sucesso no container:

```powershell
python scripts/test_demo_kit.py
```

*Saída esperada:* `[OK] Todos os scripts de demonstracao foram validados com sucesso!`

---

### Passo 11: Compilação do Artigo em LaTeX (Opcional)

Se possuir o MiKTeX ou TeX Live instalado no Windows e desejar recompilar o artigo científico:

```powershell
python scripts/compile_paper.py
```

*Saída gerada:* [paper/main.pdf](file:///c:/Users/raild/Downloads/Trabalho-Final-BD2/paper/main.pdf) validado contra o edital da SBC (exatas 10 páginas, 0 avisos de *Overfull \hbox*, figuras em 300 DPI).

---

## 4. Pipeline Completo em Comando Único no PowerShell

Para executar **todos os passos** sequencialmente de ponta a ponta sem intervenção manual no Windows PowerShell (com o ambiente virtual ativo):

```powershell
docker compose up -d --wait; `
python scripts/smoke_test.py; `
python scripts/generate_data.py; `
python scripts/create_schema.py; `
python scripts/load_baseline.py; `
python scripts/clone_optimized.py; `
python scripts/apply_optimizations.py; `
python scripts/run_benchmarks.py; `
python scripts/analyze_results.py; `
python scripts/generate_charts.py; `
python scripts/generate_plan_diagrams.py; `
python scripts/test_demo_kit.py
```

---

## 5. Guia da Demonstração Prática ao Vivo no Windows

Durante a apresentação oral, a equipe dispõe de **4 a 5 minutos** para demonstrar o contraste ao vivo de desempenho e planos de execução entre `Ecommerce_Baseline` e `Ecommerce_Otimizado`.

### Conexão via VS Code com a Extensão `SQL Server (mssql)`:

1. No VS Code, instale a extensão oficial **`SQL Server (mssql)`** (`ms-mssql.mssql`).
2. Clique no ícone do SQL Server na barra lateral e selecione **Add Connection (+)**:
   * **Server name:** `localhost,1433` (ou `127.0.0.1,1433`)
   * **Database name:** `<default>`
   * **Authentication Type:** `SQL Login`
   * **User name:** `sa`
   * **Password:** `Bd2Trabalho!2026`
   * **Save Password:** `Yes`
   * **Trust server certificate:** `True`
3. Abra os 4 scripts da pasta [scripts/demo/](file:///c:/Users/raild/Downloads/Trabalho-Final-BD2/scripts/demo/):
   * `01_q1_seek_vs_scan.sql`: Demonstra a busca pontual por e-mail saindo de *Clustered Index Scan* (2.856 leituras lógicas) para *Index Seek* (6 leituras lógicas, $<1$ ms).
   * `02_q3_indice_composto.sql`: Demonstra o ganho da ordem de chaves `(Status, DataPedido)` saindo de 8.090 leituras lógicas para 17 leituras lógicas (speedup de 87x).
   * `03_q4_eliminacao_key_lookup.sql`: Demonstra a eliminação integral do operador custoso *Key Lookup* com o índice cobridor `INCLUDE (DataPedido, ValorTotal)` (de 8.090 leituras para 5 leituras lógicas).
   * `04_w1_tradeoff_escrita.sql`: Demonstra a amplificação de escrita DML em 4 árvores B+ simultâneas (+85,33% de I/O) com `ROLLBACK` automático para preservar o dataset.
4. **Ative o Plano Real de Execução:** Pressione `Ctrl + M` (ou clique no ícone de gráfico na barra superior do editor).
5. **Execute a Consulta:** Pressione `Ctrl + Shift + E` (ou clique com botão direito > *Execute Query*).
6. O resultado tabular e os dois gráficos de planos de execução aparecerão lado a lado instantaneamente, sem travar e sem rodar nenhum comando DDL durante a apresentação!

### Conexão via SSMS (SQL Server Management Studio no Windows):

Caso prefira utilizar o SSMS no Windows:
1. Abra o SSMS e preencha a tela de conexão:
   * **Server type:** `Database Engine`
   * **Server name:** `127.0.0.1,1433`
   * **Authentication:** `SQL Server Authentication`
   * **Login:** `sa`
   * **Password:** `Bd2Trabalho!2026`
   * Em **Options >>** > aba **Connection Properties**: Marque **Trust server certificate**.
2. Abra o script `.sql` desejado.
3. Ative **Include Actual Execution Plan** (`Ctrl + M`).
4. Pressione `F5` para executar.

### Planos de Contingência:
* **Plano B (Container indisponível no projetor):** Abrir diretamente no VS Code ou SSMS os arquivos de plano de execução pré-capturados em [results/plans/](file:///c:/Users/raild/Downloads/Trabalho-Final-BD2/results/plans/) (`.sqlplan`).
* **Plano C (Falha elétrica ou de rede):** Vídeo demonstrativo de backup gravado em tela cheia da execução dos 4 scripts. Consulte [scripts/demo/README_CONTINGENCIA.md](file:///c:/Users/raild/Downloads/Trabalho-Final-BD2/scripts/demo/README_CONTINGENCIA.md).

---

## 6. Como Interpretar as Métricas e Operadores

### Métricas Principais:
* **Leituras Lógicas (`logical reads`):** Quantidade de páginas de 8 KB acessadas na memória RAM (*Buffer Pool*). É a métrica mais fidedigna e determinística em bancos de dados, pois independe de interferências transitórias de carga no processador ou no sistema operacional.
* **Tempo Decorrido (*Elapsed Time*) e CPU:** Medem a latência percebida pela aplicação e o custo em ciclos de clock de processamento.
* **Speedup:** Fator de aceleração calculado por $\frac{\text{Tempo}_{\text{Baseline}}}{\text{Tempo}_{\text{Otimizado}}}$.
* **Valor-p (*p-value*):** Calculado via Teste *t* de Student pareado ou Teste de postos com sinais de Wilcoxon. Valores $p < 0{,}001$ atestam significância estatística formal com $N=30$.

### Operadores Físicos no Plano de Execução:
* **Clustered Index Scan / Table Scan:** Varredura completa da tabela ($O(N)$). Ocorre no Baseline quando não há caminho de acesso seletivo.
* **Index Seek:** Busca binária navegando na árvore B+ do nó raiz às folhas ($O(\log_m N)$ em 2 a 4 leituras).
* **Key Lookup (Bookmark Lookup):** Busca de colunas faltantes na tabela principal quando o índice secundário não cobre todas as colunas da consulta.
* **Covering Index (`INCLUDE`):** Armazena as colunas projetadas no nível folha do índice, eliminando integralmente os Key Lookups.
* **Sort:** Operador custoso de ordenação em memória/TempDB. É eliminado quando a consulta se apoia em um índice cuja chave já está ordenada na direção do `ORDER BY`.
* **Hash Match vs. Merge / Nested Loops:** Em junções ($Q_5$), a presença de índices nas chaves estrangeiras permite substituir o custoso *Hash Match* por *Merge Join* e *Nested Loops*.

### Trade-offs Fundamentais do Trabalho:
1. **O Custo Oculto do Índice ($W_1$):** Índices secundários aceleram leituras de 10x a 400x, mas penalizam inserções em lote (+85,33% de I/O em $W_1$) devido à manutenção síncrona obrigatória de 4 árvores B+ simultâneas.
2. **Inversão de Latência em $Q_7$ (Batch Mode vs. Row Mode):** Em $Q_7$, o índice reduziu as leituras lógicas em 30,06%, mas o tempo subiu ligeiramente (de 217 ms para 364 ms) porque o SQL Server 2022 executou o *Hash Match* original em **Batch Mode on Rowstore** (vetorizado com ~900 linhas por pacote), enquanto o índice forçou um *Stream Aggregate* em **Row Mode** (linha a linha). Essa análise comprova domínio profundo dos mecanismos internos da engine.

---

## 7. Solução de Problemas Comuns no Windows

### 1. Erro: "Login failed for user 'sa' (Erro 18456)" ao rodar `apply_optimizations.py` ou `run_benchmarks.py`
* **Causa:** No SQL Server, tentar conectar a uma base de dados que **não existe** (por exemplo, `database="Ecommerce_Otimizado"`) não retorna a mensagem "banco não encontrado", mas sim o erro de segurança `18456: Login failed for user 'sa'`. Isso acontece quando o **Passo 6 (`python scripts/clone_optimized.py`)** não foi executado antes do Passo 7!
* **Solução:** Execute o Passo 6 para clonar a base a partir do backup da baseline:
  ```powershell
  python scripts/clone_optimized.py
  ```
  Assim que a clonagem terminar com sucesso, execute o Passo 7:
  ```powershell
  python scripts/apply_optimizations.py
  ```

### 2. Erro ao subir o container: "Port 1433: bind: address already in use"
* **Causa:** O Windows possui um serviço local do SQL Server (ex: `MSSQLSERVER` ou `SQLEXPRESS`) já em execução escutando na porta 1433.
* **Solução rápida:** Abra o PowerShell como Administrador e pare o serviço local:
  ```powershell
  Stop-Service -Name "MSSQLSERVER" -Force
  # Ou se for a versão Express:
  Stop-Service -Name "MSSQL$SQLEXPRESS" -Force
  ```
* **Solução alternativa:** Mudar a porta no arquivo [.env](file:///c:/Users/raild/Downloads/Trabalho-Final-BD2/.env) (ex: `MSSQL_PORT=1434`), ajustando também a porta no comando de conexão do VS Code/SSMS.

### 3. Erro: "docker: error during connect / daemon not running"
* **Causa:** O Docker Desktop não está aberto ou ainda está iniciando.
* **Solução:** Abra o aplicativo **Docker Desktop** pelo menu Iniciar e aguarde o ícone na bandeja indicar que o serviço está rodando.

### 4. Erro no PowerShell: "A execução de scripts foi desabilitada neste sistema"
* **Causa:** Política de restrição de execução padrão do PowerShell para o usuário.
* **Solução:** Execute no PowerShell:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```

### 5. MiKTeX abrindo pop-up pedindo confirmação para baixar pacotes LaTeX
* **Causa:** O MiKTeX no Windows por padrão pergunta interativamente se deve baixar pacotes ausentes.
* **Solução:** Abra o aplicativo **MiKTeX Console** > clique em **Settings** > configure **Always install missing packages on-the-fly** para `Yes`.

---

## 8. Estrutura de Diretórios do Repositório

```text
Trabalho-Final-BD2/
├── Como rodar.md                  # Este guia completo de execução no Windows
├── docker-compose.yml             # Definição do container SQL Server 2022 Developer
├── pyproject.toml                 # Metadados e dependências do projeto
├── .env.example                   # Variáveis de ambiente para porta e senha SA
├── data/                          # Diretório montado no container para os CSVs gerados
├── scripts/
│   ├── smoke_test.py              # Teste inicial de conectividade e versões
│   ├── generate_data.py           # Gerador reprodutível do dataset (seed=42)
│   ├── create_schema.py           # DDL de criação da base e tabelas iniciais
│   ├── load_baseline.py           # Carga massiva via BULK INSERT em lotes
│   ├── clone_optimized.py         # Clonagem da base gêmea via Backup/Restore
│   ├── apply_optimizations.py     # DDL dos 9 índices secundários na base otimizada
│   ├── run_benchmarks.py          # Benchmark automatizado (N=30 Warm, N=10 Cold, MAXDOP 1)
│   ├── analyze_results.py         # Consolidação estatística e testes de hipótese
│   ├── generate_charts.py         # Gerador de gráficos em alta resolução (300 DPI)
│   ├── generate_plan_diagrams.py  # Diagramação visual dos planos de execução
│   ├── compile_paper.py           # Compilador e validador do artigo SBC (<= 10 págs)
│   ├── test_demo_kit.py           # Teste automatizado dos scripts da demonstração
│   ├── sql/                       # Scripts Transact-SQL de DDL e carga
│   └── demo/                      # Scripts SQL numerados (01 a 04) para a demo ao vivo
├── paper/
│   ├── main.tex                   # Artigo científico completo no padrão SBC
│   ├── main.pdf                   # PDF compilado do artigo (exatas 10 páginas)
│   ├── sbc.bst / sbc-template.sty # Arquivos de estilo oficial da SBC
│   └── figures/                   # Figuras e gráficos em PNG de alta resolução
├── results/
│   ├── summary_table.csv          # Tabela com médias, medianas, speedups e p-valores
│   ├── summary_stats.json         # Estatísticas completas em JSON
│   └── plans/                     # Planos reais salvos em formato .sqlplan (XML)
├── slides/
│   ├── apresentacao.tex           # Slides da apresentação em LaTeX Beamer (16:9)
│   ├── apresentacao.pdf           # Slides compilados em PDF (13 slides)
│   └── roteiro-apresentacao.md    # Roteiro de fala cronometrado (17m30s)
└── cerebro/                       # Base de conhecimento e documentação detalhada
```
