# Referencial teórico (índices, plano de execução, otimização)

Tópicos obrigatórios do PDF: utilização de índices; funcionamento do plano de execução; otimização de consultas. Os itens abaixo são um roteiro de conteúdo, não texto pronto. Use a terminologia do SGBD escolhido.

## Índices
- Motivação: evitar *full table scan* e reduzir I/O.
- Estruturas: B-tree/B+-tree (principal), hash, bitmap, columnstore, full-text.
- Tipos: clustered × nonclustered, único, composto (a ordem das colunas importa), covering/INCLUDE, filtrado/parcial, funcional.
- Seletividade, cardinalidade e estatísticas.
- Quando o índice **não** é usado: função sobre a coluna, `LIKE '%x'`, conversão implícita de tipo, baixa seletividade.
- Custos: escrita (INSERT/UPDATE/DELETE), espaço, manutenção, fragmentação.
- Operadores no plano: Table/Index Scan, Index Seek, Key/RID Lookup.

## Plano de execução
- Pipeline: parsing → binding/validação → reescrita → otimizador → plano → executor.
- Otimizador baseado em custo (CBO): estatísticas/histogramas e estimativa de cardinalidade.
- Plano estimado × plano real (linhas estimadas × reais).
- Operadores: scans, seeks, junções (Nested Loops, Hash, Merge), sort, aggregate.
- Cache de planos e *parameter sniffing* (SQL Server); *bind peeking* (Oracle).
- Comandos por SGBD:
  - SQL Server: `SET SHOWPLAN_XML ON` (estimado), `SET STATISTICS XML ON` (real), `SET STATISTICS IO, TIME ON`, plano gráfico no SSMS.
  - Oracle: `EXPLAIN PLAN FOR ...` + `SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY)`; `AUTOTRACE` no SQL*Plus/SQL Developer.
  - Db2: `EXPLAIN` + `db2exfmt`.

## Otimização de consultas
- Lógica (push-down de seleção/projeção, ordem de junções) e física (escolha de caminhos de acesso).
- Técnicas: indexação adequada, predicados sargable, `EXISTS` × `IN`, evitar `SELECT *`, JOIN em vez de subconsulta correlacionada, atualização de estatísticas, particionamento, views indexadas/materializadas, hints (com cautela).
- Método: medir → analisar o plano → alterar → remedir.
- Métricas: tempo de CPU e decorrido, leituras lógicas/físicas, linhas processadas.

## Referências (conferidas)
Dados bibliográficos conferidos de memória/catálogos conhecidos; confirmar edição e páginas antes de gerar o BibTeX.
- Selinger et al. (1979). *Access Path Selection in a Relational Database Management System*. ACM SIGMOD.
- Graefe (1993). *Query Evaluation Techniques for Large Databases*. ACM Computing Surveys 25(2).
- Comer (1979). *The Ubiquitous B-Tree*. ACM Computing Surveys 11(2).
- Silberschatz, Korth, Sudarshan. *Database System Concepts* (use a edição que tiver em mãos).
- Elmasri & Navathe. *Sistemas de Banco de Dados* (edição em português disponível).
- Documentação oficial do SGBD escolhido.

Referências efetivamente citadas no paper devem ir para o `.bib`; o estilo é `sbc.bst`.
