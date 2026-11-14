# Plano de Implementacao do Projeto Completo
## Disciplina: Banco de Dados II (UFPI) - Trabalho Final

---

## 1. Visao Geral e Alinhamento com o Enunciado

O objetivo deste projeto e atender integralmente aos requisitos do Trabalho Final de Banco de Dados II (UFPI 2026.2), composto por:
1. **Artigo Cientifico (Paper):** Maximo de 10 paginas, no template da SBC em LaTeX, abordando utilizacao de indices, funcionamento do plano de execucao e otimizacao de consultas, com experimentacao pratica em SGBD comercial (Microsoft SQL Server Developer via Docker, atendendo a restricao "comercial, exceto MySQL") e dataset volumoso (peso: 7,0).
2. **Apresentacao Oral:** Maximo de 20 minutos, com demonstracao pratica dos experimentos (peso: 3,0).

Prazo de submissao do artigo: **17/11/2026**.
Apresentacao: **18 e 19/11/2026**.

---

## 2. Divisao do Projeto por Partes (Fases Sequenciais)

O projeto e estruturado em 6 partes bem delimitadas, garantindo entendimento simples, execucao reproduzivel e controle de riscos.

```
[Parte 1: Ambiente e Setup]
       |
       v
[Parte 2: Modelagem e Dataset]
       |
       v
[Parte 3: Consultas e Baseline]
       |
       v
[Parte 4: Otimizacao e Estatistica]
       |
       v
[Parte 5: Redacao do Paper SBC]
       |
       v
[Parte 6: Apresentacao e Demo]
```

---

### Parte 1: Preparacao do Ambiente e Infraestrutura Multiplataforma (Windows e Ubuntu)
**Objetivo:** Garantir que o SGBD comercial, os scripts de automacao e a cadeia de ferramentas de compilacao funcionem com paridade absoluta tanto no Microsoft Windows (10/11 via Docker Desktop) quanto no Ubuntu Linux (20.04/22.04/24.04 nativo).

* **1.1. Configuracao do Docker Multiplataforma:**
  * Criar `docker-compose.yml` utilizando a imagem oficial do Microsoft SQL Server 2022 Developer Edition (`mcr.microsoft.com/mssql/server:2022-latest`), com `ACCEPT_EULA=Y`, `MSSQL_PID=Developer` e limites de recursos compativeis.
  * Mapear volume relativo com sintaxe POSIX compativel com ambos os sistemas (`./data:/var/opt/mssql/data_import`) para acesso direto aos CSVs pelo comando Transact-SQL `BULK INSERT`.
  * No Ubuntu, assegurar permissoes adequadas na pasta `./data` para o usuario nao-root do container SQL Server (`uid 10001`) executando `mkdir -p ./data && chmod -R 777 ./data` (garantindo leitura dos CSVs e escrita do arquivo de backup `.bak`).
  * Validar inicializacao e conexao executando `SELECT @@VERSION;`.
* **1.2. Ferramental de Analise e Planos Graficos Multiplataforma:**
  * Utilizar o Visual Studio Code com a extensao oficial `SQL Server (mssql)` ou o Azure Data Studio, que operam com paridade de recursos e interface grafica tanto no Windows quanto no Ubuntu, permitindo a visualizacao nativa da arvore de operadores do plano de execucao e exportacao de XML (`SET STATISTICS XML ON`).
* **1.3. Orquestracao em Python, Reprodutibilidade e Blindagem Multiplataforma:**
  * Padronizar a execucao dos scripts via gerenciador `uv` (`uv run ...`), eliminando a necessidade de configuracao manual de ambientes virtuais ou compilacao de pacotes em ambos os sistemas.
  * Adotar o driver de conexao `pymssql`, cujas wheels pre-compiladas trazem a biblioteca FreeTDS embutida, dispensando a instalacao de drivers proprietarios ODBC da Microsoft (`msodbcsql18`), de pacotes C de sistema no Ubuntu (`unixodbc-dev`) ou de arquivos `.msi` no Windows. Realizar um *smoke test* inicial para validar a captura das mensagens de `SET STATISTICS IO, TIME ON` via `pymssql` (usando `pyodbc` como fallback documentado caso necessario).
  * Utilizar obrigatoriamente a biblioteca padrao `pathlib.Path` em todos os scripts Python para tratamento agnostico de diretorios e arquivos (prevenindo quebras por diferencas de separadores `\` vs `/`).
  * Padronizar nomes de arquivos e diretorios estritamente em letras minusculas (`snake_case`), prevenindo falhas decorrentes do sistema de arquivos sensivel a maiusculas/minusculas (*case-sensitive*) no Ubuntu ext4.
  * Configurar arquivo `.gitattributes` na raiz do repositorio para garantir terminadores de linha `LF` em scripts `.sh`, `.py` e `.tex` (`* text=auto`, `*.sh text eol=lf`, `*.py text eol=lf`), evitando o erro `/bin/bash^M: bad interpreter` no Linux.
  * Manter a portabilidade enxuta e pragmatica (Docker Compose, `uv`, `pathlib.Path` e `scripts/compile_paper.py`), evitando retrabalho em scripts auxiliares que atrase a redacao do artigo. Disponibilizar comandos universais `uv run python scripts/...` e wrappers simples (`run_all.sh` / `run_all.ps1`) se necessarios.
* **1.4. Compilacao do Artigo em LaTeX Multiplataforma:**
  * Descompactar o template oficial da SBC (`SBC_Conferences_Template___updated_sbc_template_sty_v2017__1_.zip`), que contem `sbc-template.sty`, `sbc.bst`, `main.tex` e `sbc-template.bib`.
  * Homologar a compilacao do documento nos dois ecossistemas:
    * No Windows: via MiKTeX ou TeX Live executando `pdflatex main.tex` e `bibtex main`;
    * No Ubuntu: via TeX Live (`sudo apt install texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-lang-portuguese`).
  * Criar script em Python (`scripts/compile_paper.py`) que orquestra a compilacao de forma transparente e identica em qualquer sistema operacional.

---

### Parte 2: Modelagem, Geracao e Carga do Dataset (Estrategia de Duas Bases)
**Objetivo:** Criar uma base de dados relacional com mais de 1 milhao de registros (alcancando ~6,25 milhoes de linhas para tornar o impacto dos indices inequivoco) e estruturar duas bases gemeas na mesma instancia do SQL Server (`Ecommerce_Baseline` e `Ecommerce_Otimizado`) para total isolamento, comparabilidade e facilidade de demonstracao.

* **2.1. Definicao do Esquema Relacional (E-Commerce B2C):**
  * Tabela `Clientes` (~200.000 registros): Dados cadastrais, cidade, estado, data de cadastro.
  * Tabela `Produtos` (~50.000 registros): Categoria, preco unitario, estoque.
  * Tabela `Pedidos` (~1.500.000 registros): Chave estrangeira para clientes, data do pedido, status, valor total.
  * Tabela `ItensPedido` (~4.500.000 registros): Chave estrangeira para pedidos e produtos, quantidade, preco unitario, desconto.
* **2.2. Script Gerador Reprodutivel Multiplataforma:**
  * Desenvolver script em Python (utilizando `uv` para gestao de dependencias) com geracao vetorizada em lotes via `numpy` (evitando loops lentos com `Faker` linha a linha para ~6,25M tuplas) para exportacao dos dados sinteticos em formato CSV em segundos.
  * Forcar gravacao com codificacao UTF-8 explicita (`encoding='utf-8'`) e terminadores de linha uniformes (`newline='\n'`), garantindo compatibilidade total tanto no Windows quanto no Ubuntu.
  * Fixar obrigatoriamente a semente de geracao pseudoaleatoria (`random.seed(42)` e `numpy.random.seed(42)`), assegurando que qualquer membro ou revisor possa reproduzir a mesma distribuicao de cardinalidade e seletividade.
* **2.3. Carga Massiva Otimizada na Base `Ecommerce_Baseline`:**
  * Criar a base `Ecommerce_Baseline` inicialmente apenas com as chaves primarias (ou tabelas heap/clustered basicas).
  * Configurar o banco de dados temporariamente para modelo de recuperacao simples (`ALTER DATABASE [Ecommerce_Baseline] SET RECOVERY SIMPLE;`), impedindo a explosao de espaco do arquivo de log de transacoes (`.ldf`).
  * Executar a carga massiva dos dados sinteticos utilizando `BULK INSERT` apontando para `/var/opt/mssql/data_import/`, com parametros de lote `BATCHSIZE = 100000`, `TABLOCK`, `CHECK_CONSTRAINTS` e `ROWTERMINATOR = '0x0a'`. Como o SQL Server em Linux nao suporta a clausula `CODEPAGE = '65001'` (erro `16202`), tabelas com acentuacao (`Clientes`, `Produtos`) utilizam arquivos temporarios UTF-16 (`DATAFILETYPE = 'widechar'`) e tabelas ASCII (`Pedidos`, `ItensPedido`) utilizam `DATAFILETYPE = 'char'`, garantindo preservacao integral dos acentos e quebras de linha em ambos os SOs.
  * Validar a integridade referencial e o total exato de registros em cada tabela.
* **2.4. Criacao da Base Gemea `Ecommerce_Otimizado` via Backup/Restore Nativo:**
  * Realizar um backup completo da base de baseline: `BACKUP DATABASE [Ecommerce_Baseline] TO DISK = '/var/opt/mssql/data_import/ecommerce_init.bak';`.
  * Restaurar a copia como uma nova base denominada `Ecommerce_Otimizado` (`RESTORE DATABASE [Ecommerce_Otimizado] FROM DISK = '...' WITH MOVE ...`).
  * Apos validar ambas as bases e o arquivo `.bak`, opcionalmente remover os CSVs intermediarios de `./data` para preservar espaco em disco (mantendo o script gerador com `seed=42` para reproducao).
  * **Beneficio fundamental:** Ambas as bases iniciam com um conteudo 100% identico e validado, permitindo que a `Ecommerce_Baseline` permaneca intocada (sem indices secundarios) enquanto a `Ecommerce_Otimizado` recebe os indices e melhorias.

---

### Parte 3: Catalogo de Consultas e Coleta do Baseline
**Objetivo:** Mapear cenarios reais de consultas SQL que demonstrem claramente os gargalos antes da otimizacao.

* **3.1. Definicao do Conjunto de Consultas (Q1 a Q10 e W1):**
  * `Q1 (Filtro simples em coluna nao indexada):` Busca pontual em `Clientes` por `Email` unico, demonstrando `Clustered Index Scan` vs `Index Seek`.
  * `Q2 (Filtro por faixa de datas em Pedidos):` Filtro seletivo por intervalo em `DataPedido` (ex.: `COUNT(*)` ou colunas cobertas pelo indice), avaliando custo de varredura ampla vs `Index Seek (Range)`.
  * `Q3 (Filtro composto - status do pedido e data):` `Status = 'ENTREGUE' AND DataPedido >= ...`, demonstrando impacto da ordem dos campos no indice (igualdade primeiro, faixa depois).
  * `Q4 (Consulta com projecao restrita e eliminacao de Key Lookup):` Projecao de colunas de `Pedidos` filtradas por `ClienteID`. Comparar `Baseline` (`Clustered Index Scan`), cenario intermediario com indice simples em `(ClienteID)` (`Index Seek` + `Key Lookup`) e `Otimizado` com *Covering Index* `INCLUDE (DataPedido, ValorTotal)` (eliminacao completa do `Key Lookup`).
  * `Q5 (Juncao de 3 tabelas - Clientes, Pedidos, ItensPedido):` Avaliar operadores de juncao (`Hash Match` vs `Merge Join` / `Nested Loops`) com indices nas chaves estrangeiras.
  * `Q6 (Paginacao e ordenacao - TOP N com ORDER BY):` `TOP 50 ... ORDER BY DataPedido DESC`, demonstrando eliminacao do operador `Sort` via leitura ordenada direta (*Backward/Ordered Scan*) na arvore B-Tree (observando uso de `INCLUDE` para evitar os 50 `Key Lookups`).
  * `Q7 (Agregacao e agrupamento - GROUP BY):` Agrupamento por `Status` com agregacao (`SUM(ValorTotal)`). Criar *Covering Index* `(Status) INCLUDE (ValorTotal)` na base otimizada para garantir a transicao real de `Hash Match (Aggregate)` para `Stream Aggregate` sem recair em `Clustered Index Scan`.
  * `Q8 (Busca textual - LIKE '%termo' vs LIKE 'termo%'):` Demonstrar perda de sargabilidade com curinga inicial e recuperacao de `Index Seek` com prefixo `LIKE 'termo%'`, explicitando no artigo a mudanca semantica da consulta e quando a reescrita e valida no dominio.
  * `Q9 (Predicado com funcao no WHERE, ex: YEAR(DataPedido) = 2025):` Demonstrar funcao impedindo uso do indice vs reescrita sargable em intervalo semiaberto (`DataPedido >= '2025-01-01' AND DataPedido < '2026-01-01'`).
  * `Q10 (Subconsulta correlacionada / NOT IN vs NOT EXISTS):` Otimizacao logica de consulta. Validar previamente no plano real do SQL Server se o cenario escolhido (ex.: coluna anulavel ou subconsulta correlacionada) gera planos efetivamente distintos, pois colunas `NOT NULL` podem levar o otimizador a gerar o mesmo plano `Anti Semi Join` para `NOT IN` e `NOT EXISTS`.
  * `W1 (Escrita massiva - INSERT em ItensPedido):` Avaliar o custo colateral de manutencao dos multiplos indices secundarios ativos em operacoes DML (10.000 linhas). As medicoes de `W1` serao executadas sob transacao revertida (`BEGIN TRANSACTION; ... ROLLBACK TRANSACTION;`), garantindo captura das metricas `STATISTICS IO, TIME` **exclusivamente do `INSERT` (antes do `ROLLBACK`)** e preservando o volume de dados constante nas 30 repeticoes.
* **3.2. Coleta de Metricas do Baseline e Validacao Previa de Planos:**
  * Antes da bateria automatizada de $N \ge 30$, executar 1x cada consulta em `Ecommerce_Baseline` e `Ecommerce_Otimizado` com `SET STATISTICS XML ON` para validar que todos os planos reais exibem exatamente as transformacoes de operadores esperadas.
  * Ativar `SET STATISTICS IO, TIME ON`.
  * Capturar tempo de CPU, tempo total decorrido e **total de leituras logicas** (buffer pool), tratando as leituras logicas como metrica primaria deterministica (imune a variacoes de concorrencia de CPU no host).
  * Exportar o plano de execucao real em XML e capturar o diagrama visual dos operadores em etapa separada do loop de repeticoes estatisticas.

---

### Parte 4: Otimizacao, Execucao Estatistica e Analise
**Objetivo:** Aplicar os indices especificos e reescritas exclusivamente na base `Ecommerce_Otimizado`, coletando dados suficientes para fundamentacao estatistica solida e comparando com a base `Ecommerce_Baseline`.

* **4.1. Aplicacao das Otimizacoes na Base `Ecommerce_Otimizado`:**
  * Criar indices nao-clusterizados simples, compostos, com colunas incluidas (`INCLUDE`) e filtrados diretamente na base `Ecommerce_Otimizado`. A base `Ecommerce_Baseline` e mantida estritamente sem indices secundarios, servindo de controle permanente.
  * Aplicar reescritas de consultas sargable e validar as alteracoes na arvore de operadores do plano antes do benchmark em lote.
* **4.2. Protocolo Experimental Automatizado:**
  * Desenvolver script em Python (`scripts/run_benchmarks.py`) para automacao dos testes com $N \ge 30$ repeticoes em **Warm Cache** (bateria estatistica principal, descartando rodadas iniciais de aquecimento), alternando as conexoes entre `Ecommerce_Baseline` e `Ecommerce_Otimizado`.
  * Separar a captura do plano XML (`SET STATISTICS XML ON`, executada 1x por cenario, dado que o plano e deterministico sob `MAXDOP 1`) do loop estatistico de $N \ge 30$ (`SET STATISTICS IO, TIME ON`), evitando sobrecarga de serializacao XML e mistura de result sets no driver Python.
  * Padronizar o grau de paralelismo das consultas (`OPTION (MAXDOP 1)`), eliminando variacoes transientes no numero de threads do processador.
  * Controlar o estado do cache do SQL Server:
    * *Warm Cache* ($N \ge 30$ por cenario): execucoes repetidas sequenciais apos descarte das rodadas de aquecimento, servindo de base principal para os testes de hipotese.
    * *Cold Cache* (bateria complementar calibrada, ex.: $N = 5\text{ a }10$ ou subconjunto critico caso os scans em baseline sejam muito longos): sanitizacao previa com `CHECKPOINT; DBCC DROPCLEANBUFFERS; DBCC FREEPROCCACHE;` para medir I/O fisico real em disco e tempo de compilacao/leitura fria.
* **4.3. Processamento Estatistico dos Resultados:**
  * Calcular media, mediana, desvio padrao, minimo, maximo e intervalo de confianca de 95%.
  * Executar testes de significancia estatistica para comparacao de amostras emparelhadas: Teste t de Student pareado (ou Teste de Wilcoxon caso a normalidade seja rejeitada pelo teste de Shapiro-Wilk), reportando o p-valor.
  * Calcular o speedup ($T_{antes} / T_{depois}$) e o percentual de reducao de leituras logicas de I/O (explicitando para `W1` o fator de desaceleracao / overhead percentual negativo na escrita).
  * Gerar graficos comparativos (boxplots e barras de erro) e tabelas formatadas em formato compativel com LaTeX.

---

### Parte 5: Redacao do Artigo Cientifico (Template SBC)
**Objetivo:** Estruturar e redigir o paper dentro do limite rigoroso de 10 paginas, com alta densidade tecnica e visual.

* **5.1. Estrutura das Secoes e Gestao de Espaco:**
  * **Resumo e Abstract:** Sintese dos objetivos, metodologia aplicada e principais fatores de aceleracao alcancados.
  * **Secao 1: Introducao:** Contextualizacao do papel do otimizador de consultas em ambientes corporativos e objetivos do trabalho.
  * **Secao 2: Referencial Teorico:**
    * Estrutura interna de indices (arvores B+ tree, clustered vs nonclustered, sargabilidade).
    * Arquitetura do processador de consultas e do otimizador baseado em custo (CBO).
    * Mecanismos de geracao e leitura do plano de execucao (operadores fisicos de scan, seek, lookups e juncoes).
  * **Secao 3: Metodologia Experimental:**
    * Caracterizacao do ambiente (hardware, SO, motor SQL Server 2022).
    * Descricao do dataset (entidades, atributos, volume de dados e distribuicao com seed=42).
    * Protocolo de medicao (metricas de I/O e CPU, isolamento de cache, repeticoes, MAXDOP e testes de hipotese).
  * **Secao 4: Resultados e Discussao (Estrategia Anti-Estouro de Paginas):**
    * Apresentacao de uma **tabela comparativa unificada consolidando todas as consultas (Q1 a Q10 e W1)** contendo Leituras Logicas (Antes/Depois), Reducao % (ou Overhead % em W1), Tempo de Execucao (Antes/Depois), Speedup e significancia estatistica ($p < 0.001$).
    * Selecao visual focada: incluir figuras de planos de execucao para apenas **3 a 4 cenarios altamente representativos** (exemplo: Q1 Seek vs Scan, Q3 Indice Composto, Q4 Eliminacao de Key Lookup comparando Baseline vs Indice Simples vs Covering com INCLUDE, e W1 Custo de DML).
    * Analise aprofundada do trade-off de manutencao de indices medido na operacao `W1`.
  * **Secao 5: Conclusao:** Conclusoes tecnicas e diretrizes praticas observadas.
  * **Referencias:** Obras classicas (Selinger, Graefe, Comer, Elmasri & Navathe, Silberschatz) formatadas via BibTeX (`sbc.bst`).
* **5.2. Validacao de Conformidade:**
  * Compilacao sem advertencias de overflow de margem (*Overfull \hbox*).
  * Verificacao do limite estrito de ate 10 paginas (incluindo referencias).

---

### Parte 6: Apresentacao e Demonstracao Pratica
**Objetivo:** Preparar uma exposicao de ate 20 minutos com clareza conceitual e demonstracao ao vivo funcional e segura.

* **6.1. Elaboracao dos Slides (Tempo alvo: 17 a 18 minutos):**
  * Minutos 0 a 2: Introducao e motivacao.
  * Minutos 2 a 6: Fundamentos de indices e planos de execucao.
  * Minutos 6 a 8: Metodologia e arquitetura do experimento (destacando o isolamento das bases `Ecommerce_Baseline` e `Ecommerce_Otimizado`).
  * Minutos 8 a 15: **Demonstracao Pratica Comparativa** (3 a 4 consultas executadas lado a lado em duas abas: uma na base baseline e outra na otimizada, exibindo a comparacao imediata dos planos de execucao e tempos).
  * Minutos 15 a 18: Sintese dos resultados estatisticos e trade-offs de escrita.
  * Minutos 18 a 20: Conclusoes e espaco para perguntas.
* **6.2. Kit da Demonstracao Pratica:**
  * Abas pré-configuradas no VS Code (extensão `mssql`) ou SSMS conectadas respectivamente a `Ecommerce_Baseline` e `Ecommerce_Otimizado`.
  * Scripts SQL organizados e prontos para execucao imediata sem necessidade de criar ou remover indices durante a apresentacao ao vivo (eliminando atrasos e riscos operacionais).
  * Gravacao de video de contingencia da execucao dos experimentos (backup caso ocorra falha de hardware ou atraso no dia da apresentacao).

---

## 3. Matriz de Rastreabilidade dos Requisitos

| Requisito do Enunciado (PDF) | Parte Correspondente no Plano | Criterio de Atendimento |
|---|---|---|
| Paper de no maximo 10 paginas | Parte 5 | Limite monitorado com tabela unificada e max. 3-4 figuras de planos |
| Abordar utilizacao de indices | Partes 2, 3, 4 e 5 | Teoria aprofundada e aplicacao pratica de multiplos tipos de indices |
| Funcionamento do plano de execucao | Partes 1, 3, 4 e 5 | Captura de planos reais (XML/graficos) e analise de operadores |
| Otimizacao de consultas | Partes 3, 4 e 5 | Reescrita de consultas, sargabilidade e avaliacao de ganhos |
| Template da SBC em LaTeX | Partes 1 e 5 | Utilizacao dos arquivos oficiais do pacote SBC |
| SGBD comercial (exceto MySQL) | Parte 1 | Microsoft SQL Server 2022 Developer Edition |
| Dataset com grande quantidade de registros | Parte 2 | Esquema relacional com mais de 6 milhoes de registros (seed=42) |
| Analise estatistica dos resultados | Parte 4 | N >= 30 repeticoes, media, desvio padrao, IC 95%, teste t/Wilcoxon e speedup |
| Comparacao antes e apos a otimizacao | Partes 3, 4 e 5 | Tabela detalhada de tempos e leituras logicas antes e depois |
| Apresentacao de no maximo 20 minutos | Parte 6 | Roteiro ensaiado de 17-18 minutos |
| Demonstracao pratica dos experimentos | Parte 6 | Scripts prontos no SQL Server com backup visual gravado |
| Compatibilidade Multiplataforma (Windows e Ubuntu) | Partes 1, 2, 4 e 5 | Docker Compose, Python/uv com pathlib e pymssql, comandos universais (`uv run`) e script compile_paper.py |

---

## 4. Cronograma de Execucao (13/11 a 19/11)

* **13/11 (Sexta-feira):** Conclusao e refinamento do plano; ajuste do protocolo experimental e catalogo de consultas.
* **14/11 (Sabado):** Subida do container SQL Server com volume compartilhado; extracao do template SBC e criacao do esqueleto LaTeX + `compile_paper.py`; geracao vetorizada e carga do dataset sintetico (`seed=42`, `RECOVERY SIMPLE`, `BATCHSIZE`); criacao do clone `Ecommerce_Otimizado` e dos indices; validacao previa dos planos XML reais de Q1–Q10 e W1; inicio da redacao de Introducao e Referencial Teorico.
* **15/11 (Domingo):** Execucao da bateria estatistica automatizada ($N \ge 30$ em Warm Cache + Cold Cache calibrado, `MAXDOP 1`); consolidacao dos graficos e tabelas sinteticas; calculo de testes de hipotese; redacao da Metodologia e Resultados no paper SBC.
* **16/11 (Segunda-feira):** Conclusao da redacao de Resultados, Discussao e Conclusao no paper; revisao textual e controle estrito das 10 paginas; elaboracao dos slides, kit da demonstracao (`scripts/demo/`) e gravacao do video de contingencia.
* **17/11 (Terca-feira):** Revisao final do artigo em LaTeX; compilacao definitiva e submissao do arquivo PDF.
* **18/11 e 19/11 (Quarta e Quinta-feira):** Apresentacao do trabalho e realizacao da demonstracao pratica.
