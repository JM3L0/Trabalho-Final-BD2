# Registro de Resultados Experimentais

- **Data de execucao:** 2026-11-14T01:56:59.214538+00:00
- **Motor:** `Microsoft SQL Server 2022 (RTM-CU28) (KB5125472) - 16.0.4325.4 (X64) `
- **Hardware do host:** Windows 11 Home Single Language | 12th Gen Intel Core i5-1235U (10 nucleos / 12 threads) | 15,71 GB RAM | SSD
- **Protocolo:** `OPTION (MAXDOP 1)` | Warm Cache: `N = 30` (apos `2` aquecimentos) | Cold Cache: `N = 10` (`CHECKPOINT; DBCC DROPCLEANBUFFERS; DBCC FREEPROCCACHE;`)

## Resultados Consolidados — Warm Cache (N = 30)

| Consulta | Leituras Base (med) | Leituras Otim. (med) | Reducao E/S | Tempo Base med (ms) | Tempo Otim. med (ms) | Speedup | Teste / p-valor |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Q1 | 2856 | 6 | 99.79% | 15.0 (DP 4.4) | 0.0 (DP 0.0) | >15x (<1 ms) | Wilcoxon pareado (p=1.487e-06) |
| Q2 | 8090 | 34 | 99.58% | 104.5 (DP 96.9) | 1.5 (DP 1.8) | 69.7x | Wilcoxon pareado (p=1.714e-06) |
| Q3 | 8090 | 17 | 99.79% | 87.0 (DP 17.5) | 1.0 (DP 0.6) | 87.0x | Wilcoxon pareado (p=1.69e-06) |
| Q4 | 8090 | 5 | 99.94% | 111.0 (DP 62.9) | 0.0 (DP 0.3) | >111x (<1 ms) | Wilcoxon pareado (p=1.721e-06) |
| Q5 | 28818 | 5295 | 81.63% | 450.0 (DP 19.4) | 12.0 (DP 2.4) | 37.5x | Wilcoxon pareado (p=1.709e-06) |
| Q6 | 8090 | 3 | 99.96% | 424.0 (DP 25.0) | 0.0 (DP 0.0) | >424x (<1 ms) | Wilcoxon pareado (p=1.729e-06) |
| Q7 | 8090 | 5658 | 30.06% | 217.0 (DP 11.8) | 364.0 (DP 36.0) | 0.60x | Wilcoxon pareado (p=1.726e-06) |
| Q8 | 637 | 28 | 95.60% | 114.0 (DP 3.6) | 1.0 (DP 0.4) | 114.0x | t-Student pareado (p=3.448e-45) |
| Q9 | 8090 | 1565 | 80.66% | 226.0 (DP 17.9) | 26.0 (DP 1.8) | 8.69x | Wilcoxon pareado (p=1.716e-06) |
| Q10 | 10946 | 8252 | 24.61% | 370.5 (DP 34.2) | 219.5 (DP 23.9) | 1.69x | Wilcoxon pareado (p=1.719e-06) |
| W1 | 97154 | 180057 | -85.33% | 384.0 (DP 113.9) | 404.0 (DP 853.2) | 0.95x | Wilcoxon pareado (p=0.1294) |

## Resultados Consolidados — Cold Cache (N = 10)

| Consulta | Leituras Base (med) | Leituras Otim. (med) | Reducao E/S | Tempo Base med (ms) | Tempo Otim. med (ms) | Speedup | p-valor |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Q1 | 2856 | 6 | 99.79% | 44.0 | 3.5 | 12.6x | 0.001953 |
| Q2 | 8090 | 34 | 99.58% | 281.5 | 6.0 | 46.9x | 9.361e-11 |
| Q3 | 8090 | 17 | 99.79% | 246.5 | 6.5 | 37.9x | 6.427e-11 |
| Q4 | 8090 | 5 | 99.94% | 194.0 | 2.0 | 97.0x | 2.242e-11 |
| Q5 | 28818 | 11928 | 58.61% | 1027.5 | 237.5 | 4.33x | 2.395e-07 |
| Q6 | 8090 | 3 | 99.96% | 772.0 | 2.0 | 386.0x | 2.981e-09 |
| Q7 | 8090 | 5658 | 30.06% | 402.0 | 685.0 | 0.59x | 1.638e-07 |
| Q8 | 637 | 28 | 95.60% | 207.0 | 5.0 | 41.4x | 1.036e-08 |
| Q9 | 8090 | 1565 | 80.66% | 588.0 | 74.5 | 7.89x | 5.515e-08 |
| Q10 | 10946 | 8252 | 24.61% | 715.0 | 443.0 | 1.61x | 5.152e-05 |
| W1 | 77448 | 282476 | -264.73% | 502.0 | 1098.5 | 0.46x | 0.001953 |

## Evolucao em 3 Estagios de Q4 (Eliminacao de Key Lookup)

- **Baseline (`PK_Pedidos` Clustered Scan):** `8090` leituras logicas (`111.0` ms mediano).
- **Intermediario (`IX_Pedidos_ClienteID` Seek + Key Lookup):** `1296` leituras logicas (`1` ms).
- **Covering Index (`IX_Pedidos_ClienteID_Cov` com `INCLUDE`):** `5` leituras logicas (`0.0` ms mediano, `<1 ms`).

## Achados Experimentais Criticos

- **Ganhos expressivos de E/S e latencia em leituras (`Q1`–`Q6`, `Q8`–`Q10`):** Reducoes de leituras logicas entre 24,61% (`Q10`) e 99,96% (`Q6`), com aceleracao de ate >424x (`Q6`), >111x (`Q4`) e 114x (`Q8`) em *Warm Cache*.
- **Trade-off real em `Q7` (Batch Mode vs Row Mode sob `MAXDOP 1`):** O indice de cobertura `IX_Pedidos_Status_Cov` reduziu as leituras logicas em 30,06% (8.090 para 5.658) e eliminou o *Hash Match* (e sua concessao de memoria), mas o operador `Stream Aggregate` resultante executou em *Row Mode* (364,0 ms medianos), ficando mais lento em CPU que o `Hash Match` em *Batch Mode on Rowstore* do Baseline (217,0 ms).
- **Custo de escrita em `W1`:** A manutencao de 3 indices secundarios em `ItensPedido` elevou as leituras logicas de 97.154 para 180.057 (+85,33% em *Warm Cache*) e aumentou o tempo de insercao em lote (502,0 ms para 1.098,5 ms em *Cold Cache*).
