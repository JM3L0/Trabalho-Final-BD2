# Guia da Demonstração Prática e Plano de Contingência (Subparte 6.2)

Este diretório contém o kit executável da demonstração ao vivo (Slide 12 / Página 12 de `slides/apresentacao.pdf`), com duração alvo de **4 a 5 minutos** dentro da janela total de 17m30s da apresentação (`<= 20 min` no edital).

---

## 1. Preparação Pré-Banca (10 minutos antes)

1. Confirmar que o container Docker `bd2_sqlserver` está saudável:
   ```powershell
   docker ps --filter "name=bd2_sqlserver"
   uv run python scripts/smoke_test.py
   ```
2. Executar a validação automatizada do kit antes de subir ao palco:
   ```powershell
   uv run python scripts/test_demo_kit.py
   ```
3. Abrir o VS Code no diretório raiz (`Trabalho-Final-BD2`), conectar a extensão **`ms-mssql.mssql`** ao perfil local (`127.0.0.1,1433`, usuário `sa`), abrir os 4 scripts na ordem e ativar **`Enable Actual Plan`** (`Ctrl+M` ou ícone da barra de ferramentas) em cada aba.

---

## 2. Roteiro ao Vivo (Plano A — Execução Direta no Docker)

| Ordem | Arquivo | Foco da Fala ao Vivo | O que Mostrar na Tela |
| :---: | :--- | :--- | :--- |
| 1 | `01_q1_seek_vs_scan.sql` | Custo $O(N)$ vs. $O(\log_m N)$ na busca pontual por `Email` | **Baseline:** `Clustered Index Scan` (2.856 pág.) vs. **Otimizado:** `Index Seek` + `Key Lookup` (6 pág., $<1$ ms) |
| 2 | `02_q3_indice_composto.sql` | Ordem de chaves `(Status, DataPedido)` (igualdade à esquerda, faixa à direita) | **Baseline:** `Clustered Index Scan` (8.090 pág.) vs. **Otimizado:** `Index Seek` puro em `IX_Pedidos_Status_Data` (17 pág., `1,0` ms med.) |
| 3 | `03_q4_eliminacao_key_lookup.sql` | Benefício prático de `INCLUDE (DataPedido, ValorTotal)` para eliminar 422 lookups | **Baseline:** 8.090 pág. vs. **Otimizado:** `Index Seek` puro em `IX_Pedidos_ClienteID_Cov` (5 pág., $<1$ ms) |
| 4 | `04_w1_tradeoff_escrita.sql` | Mito do "índice gratuito": amplificação síncrona em múltiplas árvores B+ sem sujar a base | Operador `Sequence` atualizando 4 B+ Trees (incluindo índice filtrado `Desconto >= 10`), elevando significativamente as leituras em `ItensPedido` (~2,7 mil $\rightarrow$ ~73 mil pág.; total ~62 mil–97 mil $\rightarrow$ ~145 mil–180 mil pág.); `COUNT(*) = 4.500.000` pós-`ROLLBACK` |

---

## 3. Plano B — Planos `.sqlplan` Pré-Capturados (Falha no Container/SQL Server)

Se o Docker Desktop ou a conexão com SQL Server falhar durante a apresentação, **não depurar em público**: abrir diretamente no VS Code (`mssql`) ou Azure Data Studio os planos XML reais já salvos e versionados no repositório:

- `results/plans/baseline/q1_baseline.sqlplan` vs. `results/plans/optimized/q1_optimized.sqlplan`
- `results/plans/baseline/q3_baseline.sqlplan` vs. `results/plans/optimized/q3_optimized.sqlplan`
- `results/plans/baseline/q4_baseline.sqlplan` $\rightarrow$ `results/plans/optimized/q4_intermediate_lookup.sqlplan` $\rightarrow$ `results/plans/optimized/q4_optimized.sqlplan` (mostra os 3 estágios de `Q4` ao vivo!)
- `results/plans/baseline/w1_baseline.sqlplan` vs. `results/plans/optimized/w1_optimized.sqlplan`

Os números exatos de resumo estatístico também estão prontos para consulta em `results/summary_table.csv`.

---

## 4. Plano C — Vídeo de Contingência em MP4 (Ação Manual Pré-Banca)

> **Ação obrigatória da equipe antes de 18–19/11/2026:** gravar em tela cheia (ex.: OBS Studio ou Xbox Game Bar `Win+Alt+R`) um vídeo único (~4m30s, sem áudio ou narrado em off) executando `01_q1_seek_vs_scan.sql` até `04_w1_tradeoff_escrita.sql` com *Actual Execution Plan* e a aba *Messages* (`STATISTICS IO, TIME ON`) visíveis, salvando localmente como `slides/demo_backup_local.mp4` (fora do Git se exceder tamanho ou em pendrive de backup).
