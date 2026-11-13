# Catalogo de Consultas de Benchmark (Q1 a Q10 e W1)

Esquema: E-Commerce B2C (`Clientes`, `Produtos`, `Pedidos`, `ItensPedido` com ~6,25 milhoes de registros).  
Todas as consultas utilizam `OPTION (MAXDOP 1)` para padronizacao estatistica.

| ID | Cenario de Negocio e SQL | Diagnostico Baseline (`Ecommerce_Baseline`) | Otimizacao (`Ecommerce_Otimizado`) | Transformacao no Plano de Execucao |
|---|---|---|---|---|
| **Q1** | Busca por cliente por e-mail ou documento unico | Varredura completa (*Clustered Index Scan*) em 200k tuplas | Criacao de indice nao-clusterizado `IX_Clientes_Email` | Substituicao de *Scan* por *Index Seek* pontual |
| **Q2** | Extrato de pedidos por intervalo de datas (`DataPedido BETWEEN ...`) | Varredura completa (*Clustered Index Scan*) em 1,5M tuplas | Criacao de indice nao-clusterizado em `DataPedido` | Substituicao de *Scan* por *Index Seek (Range)* |
| **Q3** | Pedidos filtrados por status e intervalo de datas (`Status = 'ENTREGUE' AND DataPedido >= ...`) | Varredura ampla ou busca parcial ineficiente | Indice composto `IX_Pedidos_Status_Data` (ordem: igualdade primeiro, faixa depois) | *Index Seek* composto com seletividade maxima |
| **Q4** | Projecao de colunas especificas de pedidos por cliente (`ClienteID`, `DataPedido`, `ValorTotal`) | *Index Seek* seguido por alto volume de *Key Lookup* (Bookmark Lookup) na PK | Indice cobridor (*Covering Index*) com clausula `INCLUDE (DataPedido, ValorTotal)` | Eliminacao completa de *Key Lookup* (consulta 100% resolvida no indice) |
| **Q5** | Relatorio consolidado com juncao de `Clientes`, `Pedidos` e `ItensPedido` | Operadores de juncao custosos em memoria/disco (*Hash Match*) | Criacao de indices nas FKs (`ClienteID`, `PedidoID`, `ProdutoID`) | Substituicao de *Hash Match* por *Merge Join* ou *Nested Loops* |
| **Q6** | Paginacao de pedidos mais recentes (`TOP 50 ... ORDER BY DataPedido DESC`) | Execucao com operador de alto custo de ordenacao explicita (*Sort*) | Indice nao-clusterizado ordenado `(DataPedido DESC)` | Eliminacao do operador *Sort* (leitura ordenada direta pelo indice) |
| **Q7** | Agregacao e consolidacao de faturamento por status (`GROUP BY Status`) | Agrupamento em tabela hash (*Hash Aggregate*) | Indice sobre a coluna de agrupamento | Substituicao de *Hash Match* por *Stream Aggregate* |
| **Q8** | Busca textual de produtos: `LIKE '%termo'` vs `LIKE 'termo%'` | Perda total de sargabilidade (*Table/Index Scan*) | Reescrita para predicado com curinga terminal `LIKE 'termo%'` + indice | Habilitacao de *Index Seek* (sargabilidade recuperada) |
| **Q9** | Filtro temporal com funcao no WHERE (`YEAR(DataPedido) = 2025`) | Funcao aplicada a cada linha impede o uso de indices (*Index Scan*) | Reescrita sargable para intervalo fechado (`DataPedido >= '2025-01-01' AND ...`) | Recuperacao do *Index Seek* |
| **Q10** | Clientes sem pedidos: subconsulta correlacionada `NOT IN` vs `NOT EXISTS` | Plano ineficiente com tratamento defensivo de NULLs | Reescrita logica com `NOT EXISTS` ou `LEFT JOIN ... WHERE PedidoID IS NULL` | Reorganizacao da arvore de operadores para juncao anti-semantica eficiente |
| **W1** | Insercao massiva de lote em `ItensPedido` (10.000 registros) | Insercao rapida (apenas manutencao da PK basica) | Insercao com multiplos indices secundarios ativos | Medicao do overhead real de I/O e CPU para manutencao de arvores B+ tree (executado com `BEGIN TRAN ... ROLLBACK TRAN`) |

---

## Protocolo de Execucao por Linha
1. Captura do plano real em XML (`SET STATISTICS XML ON`) e captura grafica (SVG/PNG) no cliente SQL.
2. Medicao de leituras logicas e tempos via `SET STATISTICS IO, TIME ON`.
3. Execucao de $N \ge 30$ repeticoes para o calculo da analise estatistica formal (media, desvio, IC 95% e teste pareado).
