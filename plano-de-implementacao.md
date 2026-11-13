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
  * Adotar o driver de conexao `pymssql`, cujas wheels pre-compiladas trazem a biblioteca FreeTDS embutida, dispensando a instalacao de drivers proprietarios ODBC da Microsoft (`msodbcsql18`), de pacotes C de sistema no Ubuntu (`unixodbc-dev`) ou de arquivos `.msi` no Windows.
  * Utilizar obrigatoriamente a biblioteca padrao `pathlib.Path` em todos os scripts Python para tratamento agnostico de diretorios e arquivos (prevenindo quebras por diferencas de separadores `\` vs `/`).
  * Padronizar nomes de arquivos e diretorios estritamente em letras minusculas (`snake_case`), prevenindo falhas decorrentes do sistema de arquivos sensivel a maiusculas/minusculas (*case-sensitive*) no Ubuntu ext4.
  * Configurar arquivo `.gitattributes` na raiz do repositorio para garantir terminadores de linha `LF` em scripts `.sh`, `.py` e `.tex` (`* text=auto`, `*.sh text eol=lf`, `*.py text eol=lf`), evitando o erro `/bin/bash^M: bad interpreter` no Linux.
  * Disponibilizar scripts de disparo rapido compativeis com cada terminal:
    * `bash run_all.sh` (ou `./run_all.sh` com terminacao LF) para Ubuntu/Linux;
    * `powershell -ExecutionPolicy Bypass -File .\run_all.ps1` para Windows PowerShell;
    * Comandos universais padrao `uv run python scripts/...` agnosticos de sistema operacional.
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
  * Desenvolver script em Python (utilizando `uv` para gestao de dependencias) para geracao dos dados sinteticos em formato CSV.
  * Forcar gravacao com codificacao UTF-8 explicita (`encoding='utf-8'`) e terminadores de linha uniformes (`newline='\n'`), garantindo compatibilidade total tanto no Windows quanto no Ubuntu.
  * Fixar obrigatoriamente a semente de geracao pseudoaleatoria (`random.seed(42)` e `numpy.random.seed(42)`), assegurando que qualquer membro ou revisor possa reproduzir a mesma distribuicao de cardinalidade e seletividade.
* **2.3. Carga Massiva Otimizada na Base `Ecommerce_Baseline`:**
  * Criar a base `Ecommerce_Baseline` inicialmente apenas com as chaves primarias (ou tabelas heap/clustered basicas).
  * Configurar o banco de dados temporariamente para modelo de recuperacao simples (`ALTER DATABASE [Ecommerce_Baseline] SET RECOVERY SIMPLE;`), impedindo a explosao de espaco do arquivo de log de transacoes (`.ldf`).
  * Executar a carga massiva dos dados sinteticos utilizando `BULK INSERT` apontando para `/var/opt/mssql/data_import/`, com parametros de lote e codificacao: `BATCHSIZE = 100000`, `DATAFILETYPE = 'char'`, `CODEPAGE = '65001'` e `ROWTERMINATOR = '0x0a'`, garantindo leitura precisa dos acentos e quebras de linha em ambos os SOs.
  * Validar a integridade referencial e o total exato de registros em cada tabela.
* **2.4. Criacao da Base Gemea `Ecommerce_Otimizado` via Backup/Restore Nativo:**
  * Realizar um backup completo da base de baseline: `BACKUP DATABASE [Ecommerce_Baseline] TO DISK = '/var/opt/mssql/data_import/ecommerce_init.bak';`.
  * Restaurar a copia como uma nova base denominada `Ecommerce_Otimizado` (`RESTORE DATABASE [Ecommerce_Otimizado] FROM DISK = '...' WITH MOVE ...`).
  * **Beneficio fundamental:** Ambas as bases iniciam com um conteudo 100% identico e validado, permitindo que a `Ecommerce_Baseline` permaneca intocada (sem indices secundarios) enquanto a `Ecommerce_Otimizado` recebe os indices e melhorias.

---

### Parte 3: Catalogo de Consultas e Coleta do Baseline
**Objetivo:** Mapear cenarios reais de consultas SQL que demonstrem claramente os gargalos antes da otimizacao.

* **3.1. Definicao do Conjunto de Consultas (Q1 a Q10 e W1):**
  * `Q1 (Filtro simples em coluna nao indexada):` Demonstrar Table Scan / Clustered Index Scan.
  * `Q2 (Filtro por faixa de datas em Pedidos):` Avaliar custo de varredura ampla.
  * `Q3 (Filtro composto - status do pedido e data):` Demonstrar impacto da ordem dos campos no indice.
  * `Q4 (Consulta com projecao restrita):` Preparar cenario para indice de cobertura com clausula `INCLUDE` (eliminando Key Lookup).
  * `Q5 (Juncao de 3 tabelas - Clientes, Pedidos, ItensPedido):` Avaliar operadores de juncao (Hash Match vs Nested Loops).
  * `Q6 (Paginacao e ordenacao - TOP N com ORDER BY):` Demonstrar eliminacao do operador de custo elevado `Sort`.
  * `Q7 (Agregacao e agrupamento - GROUP BY):` Avaliar Stream Aggregate vs Hash Aggregate.
  * `Q8 (Busca textual - LIKE '%termo' vs LIKE 'termo%'):` Demonstrar perda de sargabilidade.
  * `Q9 (Predicado com funcao no WHERE, ex: YEAR(Data)):` Demonstrar o problema de funcoes impedindo o uso de indices.
  * `Q10 (Subconsulta correlacionada vs JOIN/EXISTS):` Otimizacao logica da consulta.
  * `W1 (Escrita massiva - INSERT/UPDATE):` Avaliar o custo colateral de manutencao dos indices em operacoes DML. As medicoes de W1 serao executadas sob transacao revertida (`BEGIN TRANSACTION; ... ROLLBACK TRANSACTION;`), garantindo que o volume de dados permaneca constante em todas as repeticoes estatisticas.
* **3.2. Coleta de Metricas do Baseline:**
  * Ativar `SET STATISTICS IO, TIME ON`.
  * Capturar tempo de CPU, tempo total decorrido e **total de leituras logicas** (buffer pool), tratando as leituras logicas como metrica primaria deterministica (imune a variacoes de concorrencia de CPU no host).
  * Exportar o plano de execucao real em XML e capturar o diagrama visual dos operadores antes da intervencao.

---

### Parte 4: Otimizacao, Execucao Estatistica e Analise
**Objetivo:** Aplicar os indices especificos e reescritas exclusivamente na base `Ecommerce_Otimizado`, coletando dados suficientes para fundamentacao estatistica solida e comparando com a base `Ecommerce_Baseline`.

* **4.1. Aplicacao das Otimizacoes na Base `Ecommerce_Otimizado`:**
  * Criar indices nao-clusterizados simples, compostos, com colunas incluidas (`INCLUDE`) e filtrados diretamente na base `Ecommerce_Otimizado`. A base `Ecommerce_Baseline` e mantida estritamente sem indices secundarios, servindo de controle permanente.
  * Aplicar reescritas de consultas sargable e analisar as alteracoes na arvore de operadores do plano.
* **4.2. Protocolo Experimental Automatizado:**
  * Desenvolver script em Python para automacao dos testes com $N \ge 30$ repeticoes para cada cenario, alternando as conexoes entre `Ecommerce_Baseline` e `Ecommerce_Otimizado`.
  * Padronizar o grau de paralelismo das consultas (`OPTION (MAXDOP 1)` ou grau fixo documentado), eliminando variacoes transientes no numero de threads do processador.
  * Controlar o estado do cache do SQL Server:
    * Medicoes em *Cold Cache* com `CHECKPOINT; DBCC DROPCLEANBUFFERS;` (e `DBCC FREEPROCCACHE;` quando recompilacao for avaliada).
    * Medicoes em *Warm Cache* (execucoes repetidas sequenciais, descartando a execucao inicial de aquecimento).
* **4.3. Processamento Estatistico dos Resultados:**
  * Calcular media, mediana, desvio padrao, minimo, maximo e intervalo de confianca de 95%.
  * Executar testes de significancia estatistica para comparacao de amostras emparelhadas: Teste t de Student pareado (ou Teste de Wilcoxon caso a normalidade seja rejeitada pelo teste de Shapiro-Wilk), reportando o p-valor.
  * Calcular o speedup ($T_{antes} / T_{depois}$) e o percentual de reducao de leituras logicas de I/O.
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
    * Apresentacao de uma **tabela comparativa unificada consolidando todas as consultas (Q1 a Q10 e W1)** contendo Leituras Logicas (Antes/Depois), Reducao %, Tempo de Execucao (Antes/Depois), Speedup e significancia estatistica ($p < 0.001$).
    * Selecao visual focada: incluir figuras de planos de execucao para apenas **3 a 4 cenarios altamente representativos** (exemplo: Q1 Seek vs Scan, Q3 Indice Composto, Q4 Eliminacao de Key Lookup com INCLUDE e W1 Custo de DML).
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
| Compatibilidade Multiplataforma (Windows e Ubuntu) | Partes 1, 2, 4 e 5 | Docker Compose, Python/uv com pathlib e pymssql, scripts dual (sh/ps1) e script compile_paper.py |

---

## 4. Cronograma de Execucao (13/11 a 19/11)

* **13/11 (Sexta-feira):** Conclusao do plano; subida do container SQL Server com volume compartilhado; geracao e carga do dataset sintetico (seed=42, recovery simple, batchsize); teste de compilacao do template SBC.
* **14/11 (Sabado):** Execucao dos experimentos de baseline (Q1 a Q10 e W1); aplicacao dos indices e otimizacoes; execucao das rodadas estatisticas ($N \ge 30$, MAXDOP controlado).
* **15/11 (Domingo):** Consolidacao dos graficos e tabelas sinteticas; calculo de testes de hipotese; redacao completa do referencial teorico e da metodologia no paper SBC.
* **16/11 (Segunda-feira):** Redacao dos resultados e discussao no paper; revisao textual e controle estrito das 10 paginas; elaboracao dos slides e do roteiro da demonstracao.
* **17/11 (Terca-feira):** Revisao final do artigo em LaTeX; compilacao e submissao do arquivo PDF.
* **18/11 e 19/11 (Quarta e Quinta-feira):** Apresentacao do trabalho e realizacao da demonstracao pratica.
