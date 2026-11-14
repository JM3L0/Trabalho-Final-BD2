# Ambiente: SGBD, Infraestrutura Multiplataforma e Dataset

## 1. SGBD Definido (Restricao do PDF: comercial, exceto MySQL)
* **Escolha:** **Microsoft SQL Server 2022 Developer Edition** em container Docker (`mcr.microsoft.com/mssql/server:2022-latest`, `MSSQL_PID=Developer`).
* **Justificativa:** Conforme [comparativo-sgbds.md](../../comparativo-sgbds.md), e formalmente comercial, gratuito para estudo e desenvolvimento, sem limitacao de tamanho de dados (ao contrario do Express), com suporte nativo a planos graficos e metricas exatas (`SET STATISTICS IO, TIME ON` e `SET STATISTICS XML ON`).
* **Estrategia de Duas Bases na Mesma Instancia:**
  * `Ecommerce_Baseline`: Base com dados carregados e apenas chaves primarias (ou tabelas heap/clustered basicas), sem indices secundarios, servindo de grupo de controle cientifico permanente.
  * `Ecommerce_Otimizado`: Base clonada da baseline via `BACKUP DATABASE` e `RESTORE DATABASE ... WITH MOVE`, recebendo todos os indices secundarios, indices com `INCLUDE`, indices filtrados e consultas otimizadas.
  * **Vantagem de Execucao:** Permite abrir duas abas no cliente SQL (uma em cada base) e comparar o plano de execucao e o tempo lado a lado na apresentacao de 20 min sem necessidade de criar ou remover indices ao vivo.

---

## 2. Compatibilidade Multiplataforma (Windows e Ubuntu)

O ambiente e os scripts foram projetados para serem executados com paridade total tanto no **Microsoft Windows** (10/11 via Docker Desktop) quanto no **Ubuntu Linux** (20.04/22.04/24.04 nativo via Docker Engine):

* **Docker Multiplataforma:**
  * No Windows: Executado via Docker Desktop (backend WSL2).
  * No Ubuntu: Executado via Docker Engine ou Docker Desktop para Linux.
  * O arquivo `docker-compose.yml` utiliza mapeamento relativo POSIX (`./data:/var/opt/mssql/data_import`) compativel com ambos os sistemas operacionais.
  * No Ubuntu, permissao de leitura e escrita garantida para o usuario nao-root do SQL Server (`uid 10001`): `mkdir -p ./data && chmod -R 777 ./data` (necessario tanto para leitura dos CSVs quanto para escrita do arquivo de backup `.bak`).
* **Orquestracao em Python via `uv`:**
  * Uso de `uv run` como executor padronizado, dispensando configuracao manual de ambientes virtuais em ambos os sistemas.
  * Manipulacao de arquivos usando exclusivamente `pathlib.Path` para evitar conflito de separadores de caminho (`\` vs `/`).
  * Utilizacao da biblioteca `pymssql` (com FreeTDS pre-compilado em suas wheels), eliminando a necessidade de instalacao manual de pacotes de desenvolvimento C (`unixodbc-dev`) no Ubuntu ou drivers `.msi` no Windows. Validar em *smoke test* inicial a captura das mensagens de `SET STATISTICS IO, TIME ON` via `pymssql` (mantendo `pyodbc` como fallback se necessario).
  * Padronizacao rigorosa de nomes de arquivos em letras minusculas (`snake_case`) para evitar problemas com *case-sensitivity* no Linux ext4.
* **Scripts de Suporte e Git:**
  * Configuracao de `.gitattributes` para forcar terminadores de linha `LF` (`*.sh text eol=lf`, `*.py text eol=lf`).
  * Priorizar comandos diretos agnosticos em Python (`uv run python scripts/...`), mantendo wrappers enxutos (`run_all.sh` / `run_all.ps1`) apenas se nao duplicarem esforco antes do artigo.
* **Compilacao de LaTeX:**
  * No Windows: Suportado via MiKTeX ou TeX Live (`pdflatex`).
  * No Ubuntu: Suportado via pacote TeX Live (`sudo apt install texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-lang-portuguese`).
  * Script centralizador `scripts/compile_paper.py` compativel com ambos os ecossistemas.

---

## 3. Dataset Definido: E-Commerce B2C Sintetico (~6,25 Milhoes de Registros)

* **Origem:** Geracao sintetica vetorizada em lotes com `numpy` (evitando loops lentos com `Faker`) via script Python reprodutivel com semente fixa (`seed=42`).
* **Tamanho total:** ~6.250.000 tuplas relacionais distribuidas em 4 tabelas:
  1. `Clientes` (~200.000 registros): `ClienteID` (PK), `Nome`, `Email`, `Cidade`, `Estado`, `DataCadastro`.
  2. `Produtos` (~50.000 registros): `ProdutoID` (PK), `Nome`, `Categoria`, `Preco`, `Estoque`.
  3. `Pedidos` (~1.500.000 registros): `PedidoID` (PK), `ClienteID` (FK), `DataPedido`, `Status`, `ValorTotal`.
  4. `ItensPedido` (~4.500.000 registros): `ItemPedidoID` (PK), `PedidoID` (FK), `ProdutoID` (FK), `Quantidade`, `PrecoUnitario`, `Desconto`.
* **Volume em disco estimado:** ~1,5 GB a 2,2 GB (somando ambas as bases `Ecommerce_Baseline`, `Ecommerce_Otimizado` e o arquivo `.bak` compactado). Apos validar ambas as bases e o backup `ecommerce_init.bak`, os CSVs temporarios em `./data` podem ser removidos para liberar disco.
* **Diretrizes de Carga Massiva Otimizada:**
  * Mapeamento de volume Docker: `./data:/var/opt/mssql/data_import`.
  * Modelo de recuperacao: `ALTER DATABASE [Ecommerce_Baseline] SET RECOVERY SIMPLE;` para evitar crescimento excessivo do arquivo de log (`.ldf`).
  * Carga via `BULK INSERT` com `BATCHSIZE = 100000`, `DATAFILETYPE = 'char'`, `CODEPAGE = '65001'` e `ROWTERMINATOR = '0x0a'`.
