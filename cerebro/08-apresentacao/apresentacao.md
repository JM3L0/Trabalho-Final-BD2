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
* **Contingencia (Plano B):**
  * Gravacao prévia de video demonstrativo com captura de tela e audio, alem de capturas estaticas em alta resolucao dos planos de execucao, garantindo backup total contra falhas eletricas ou de rede no local da apresentacao.
