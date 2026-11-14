# Catalogo de Consultas de Benchmark (Q1 a Q10 e W1)

Esquema: E-Commerce B2C (`Clientes`, `Produtos`, `Pedidos`, `ItensPedido` com ~6,25 milhoes de registros).  
Todas as consultas utilizam `OPTION (MAXDOP 1)` para padronizacao estatistica.

| ID | Cenario de Negocio e SQL | Diagnostico Baseline (`Ecommerce_Baseline`) | Otimizacao (`Ecommerce_Otimizado`) | Transformacao no Plano de Execucao |
|---|---|---|---|---|
| **Q1** | Busca por cliente por `Email` unico | Varredura completa (*Clustered Index Scan*) em 200k tuplas | Criacao de indice nao-clusterizado `IX_Clientes_Email` | Substituicao de *Scan* por *Index Seek* pontual |
| **Q2** | Extrato de pedidos por intervalo seletivo de datas (`DataPedido BETWEEN ...`) | Varredura completa (*Clustered Index Scan*) em 1,5M tuplas | Criacao de indice nao-clusterizado `IX_Pedidos_DataPedido` (consulta com projecao coberta por `PedidoID`/`DataPedido`) | Substituicao de *Scan* por *Index Seek (Range)* sem *Key Lookup* |
| **Q3** | Pedidos filtrados por status e intervalo de datas (`Status = 'ENTREGUE' AND DataPedido >= ...`) | Varredura ampla (*Clustered Index Scan*) | Indice composto `IX_Pedidos_Status_Data` (ordem: igualdade primeiro, faixa depois) | *Index Seek* composto com seletividade maxima |
| **Q4** | Projecao de colunas especificas de pedidos por cliente (`ClienteID`, `DataPedido`, `ValorTotal`) | Baseline: *Clustered Index Scan* (e cenario intermediario com indice simples `(ClienteID)` gerando *Index Seek* + *Key Lookup*) | Indice cobridor (*Covering Index*) `IX_Pedidos_ClienteID_Cov` com `INCLUDE (DataPedido, ValorTotal)` | Eliminacao completa de *Key Lookup* (consulta 100% resolvida no indice) |
| **Q5** | Relatorio consolidado com juncao de `Clientes`, `Pedidos` e `ItensPedido` | Operadores de juncao custosos em memoria/disco (*Hash Match*) | Criacao de indices nas FKs (`Pedidos(ClienteID)`, `ItensPedido(PedidoID)`, `ItensPedido(ProdutoID)`) | Substituicao de *Hash Match* por *Merge Join* ou *Nested Loops* |
| **Q6** | Paginacao de pedidos mais recentes (`TOP 50 ... ORDER BY DataPedido DESC`) | Execucao com operador de alto custo de ordenacao explicita (*Sort*) | Uso da B-Tree ordenada em `DataPedido` (suporte nativo a *Backward Scan*, com `INCLUDE` caso necessario evitar os 50 *Key Lookups*) | Eliminacao do operador *Sort* (leitura ordenada direta pelo indice) |
| **Q7** | Agregacao e consolidacao de faturamento por status (`GROUP BY Status`, `SUM(ValorTotal)`) | Agrupamento em tabela hash (*Hash Match Aggregate*) | *Covering Index* `IX_Pedidos_Status_Cov (Status) INCLUDE (ValorTotal)` (evita que o otimizador recue para `Hash` por custo de *Key Lookup*) | Substituicao de *Hash Match* por *Stream Aggregate* |
| **Q8** | Busca textual de produtos: `LIKE '%termo'` vs `LIKE 'termo%'` | Perda total de sargabilidade (*Clustered Index Scan*) | Indice em `Produtos(Nome)` + reescrita para prefixo `LIKE 'termo%'` (documentando no artigo a mudanca semantica prefixo vs substring) | Habilitacao de *Index Seek* (sargabilidade recuperada) |
| **Q9** | Filtro temporal com funcao no WHERE (`YEAR(DataPedido) = 2025`) | Funcao aplicada a cada linha impede o uso de indices (*Scan*) | Reescrita sargable para intervalo semiaberto (`DataPedido >= '2025-01-01' AND DataPedido < '2026-01-01'`) | Recuperacao do *Index Seek* |
| **Q10** | Clientes sem pedidos: subconsulta correlacionada / `NOT IN` vs `NOT EXISTS` | Plano subotimo ou custoso (validar no plano real se a nulabilidade/correlacao gera planos distintos no SQL Server) | Reescrita logica com `NOT EXISTS` ou `LEFT JOIN ... WHERE PedidoID IS NULL` | Reorganizacao da arvore de operadores para juncao anti-semantica eficiente |
| **W1** | Insercao massiva de lote em `ItensPedido` (10.000 registros) | Insercao rapida (apenas manutencao da PK basica) | Insercao com multiplos indices secundarios ativos em `ItensPedido` | Medicao do overhead real (speedup < 1 / aumento de I/O e CPU) para manutencao de B+ trees (capturando `STATISTICS IO, TIME` apenas do `INSERT`, antes do `ROLLBACK`) |

---

## Protocolo de Execucao por Linha
1. Passada unica (`1x`) com `SET STATISTICS XML ON` para validar todos os planos reais esperados (incluindo o cenario intermediario com *Key Lookup* em Q4) e capturar diagramas graficos (SVG/PNG).
2. Loop estatistico separado ($N \ge 30$ em *Warm Cache* + bateria calibrada em *Cold Cache*) usando exclusivamente `SET STATISTICS IO, TIME ON`.
3. Calculo de media, desvio padrao, IC 95% e teste pareado (*t* de Student ou Wilcoxon).
