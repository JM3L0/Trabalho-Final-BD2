# Apresentacao Oral (<= 20 min) e Demonstracao Pratica

## 1. Roteiro Cronometrado (Alvo Real: 17 a 18 minutos)

| Minutos | Bloco Tematico | Conteudo e Destaques |
|---|---|---|
| **0 a 2** | Introducao e Motivacao | Problema de desempenho em grandes volumes e papel do otimizador de consultas |
| **2 a 6** | Fundamentacao Teorica | Arvores B+ tree, custo de Scans vs Seeks, geracao de planos de execucao e sargabilidade |
| **6 a 8** | Metodologia e Infraestrutura | SGBD comercial (SQL Server 2022 Developer), dataset de 6,25M tuplas e arquitetura de duas bases gemeas (`Ecommerce_Baseline` e `Ecommerce_Otimizado`) |
| **8 a 15** | **Demonstracao Pratica Comparativa** | Execucao ao vivo lado a lado de 3 a 4 consultas de alto impacto, contrastando planos de execucao e tempos |
| **15 a 17** | Analise dos Resultados e Trade-off | Apresentacao da tabela unificada, speedups alcancados e custo de manutencao em operacoes DML (W1) |
| **17 a 18** | Conclusao e Diretrizes | Principais licoes aprendidas e boas praticas de engenharia de banco de dados |
| **18 a 20** | Encerramento e Perguntas | Espaco de seguranca para arguicao da banca examinadora |

---

## 2. Estrategia da Demonstracao Pratica (Blindagem Operacional)

A adocao das duas bases de dados pre-configuradas elimina o maior risco de falha em apresentacoes ao vivo:

* **Zero Operacoes DDL ao Vivo:**
  * Nao sera necessario executar comandos de criacao (`CREATE INDEX`) ou descarte (`DROP INDEX`) durante a apresentacao.
  * Tabelas com 4,5 milhoes de tuplas exigiriam dezenas de segundos para indexacao, consumindo tempo precioso da fala.
* **Layout Lado a Lado (Split Screen):**
  * Abrir o cliente SQL (VS Code com extensao `mssql`, Azure Data Studio ou SSMS) com tela dividida:
    * Painel Esquerdo: Conectado a `Ecommerce_Baseline` (execucao da consulta exibindo plano com Scan / Key Lookup / Hash Match);
    * Painel Direito: Conectado a `Ecommerce_Otimizado` (execucao da mesma consulta exibindo resposta em milissegundos e plano otimizado com Seek / Index with INCLUDE).
* **Scripts Prontos e Numerados:**
  * Pasta `scripts/demo/` contendo arquivos autoexplicativos:
    * `01_q1_seek_vs_scan.sql`
    * `02_q3_indice_composto.sql`
    * `03_q4_eliminacao_key_lookup.sql`
    * `04_w1_tradeoff_escrita.sql`
* **Contingencia (Planos B e C):**
  * **Plano B (Offline XML):** abertura direta dos `.sqlplan` pre-capturados em `results/plans/` (23 no acervo completo, com 9 destacados para `Q1`, `Q3`, `Q4` e `W1` em [README_CONTINGENCIA.md](../../scripts/demo/README_CONTINGENCIA.md)).
  * **Plano C (Video Backup — acao manual da equipe):** gravacao previa em tela cheia (`slides/demo_backup_local.mp4`) antes da apresentacao em **18–19/11/2026**, garantindo backup total contra falhas de Docker, rede ou projetor.

---

## 3. Materiais Produzidos (Concluido em 14/11/2026)
* **Slides Beamer 16:9:** [apresentacao.tex](../../slides/apresentacao.tex) e [apresentacao.pdf](../../slides/apresentacao.pdf) (**13 paginas**, `1.485.698` bytes, 0 warnings/overfulls), cobrindo motivacao, B+ Trees, otimizador, metodologia, resultados (*Warm* e *Cold*), planos `ShowPlanXML`, demonstracao ao vivo, trade-offs (`Q7` e `W1`) e conclusoes.
* **Roteiro Cronometrado Final:** [roteiro-apresentacao.md](../../slides/roteiro-apresentacao.md) (**17m30s** totais, posicionando a demo ao vivo na Pagina 12 entre 11m30s e 16m00s, com 2m30s de margem para arguicao).
* **Kit Validado:** os 4 scripts em `scripts/demo/` foram validados contra ambas as bases via [test_demo_kit.py](../../scripts/test_demo_kit.py) com integridade pos-rollback confirmada (`4.500.000` linhas em `dbo.ItensPedido`).
