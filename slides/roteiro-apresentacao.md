# Roteiro Cronometrado da Apresentação Oral (Trabalho Final BD II)

- **Tempo limite do edital:** <= 20 minutos (apresentação + demonstração prática).
- **Tempo planejado:** **17m30s** (folga de 2m30s para perguntas e imprevistos).
- **Material:** [apresentacao.pdf](apresentacao.pdf) (13 slides Beamer 16:9) + 4 scripts em `scripts/demo/` no VS Code (`ms-mssql.mssql`).

| Página do PDF (Seção) | Bloco | Duração | Acumulado | Pontos-chave de Fala |
| :--- | :--- | :---: | :---: | :--- |
| Pág. 1 (Capa) | Capa e Contexto | 0m30s | 0m30s | Apresentação da equipe, UFPI/CSHNB, tema: indexação, planos e otimização no SQL Server 2022. |
| Pág. 2–4 (Seções 1–3) | Motivação e Teoria | 3m30s | 4m00s | Por que *Table Scan* e *Key Lookup* custam caro; árvore B+ (`INCLUDE`, composto, filtrado); sargabilidade e *Batch Mode on Rowstore* vs. *Row Mode*. |
| Pág. 5–6 (Seções 4–5) | Metodologia e Protocolo | 2m00s | 6m00s | Bases gêmeas via `BACKUP/RESTORE` (6,25M linhas, `seed=42`, 0 vs. 9 índices); `MAXDOP 1`, Warm ($N=30$) vs. Cold ($N=10$), Shapiro-Wilk + t/Wilcoxon, `W1` em rollback. |
| Pág. 7–10 (Seções 6–9) | Resultados e Planos | 4m00s | 10m00s | Reduções até 99,96% (`Q6`) e $>424\times$; evolução de 3 estágios em `Q4` (8.090 $\rightarrow$ 1.296 $\rightarrow$ 5 páginas); leitura das árvores `.sqlplan`. |
| Pág. 11 (Seção 10) | Trade-offs (`Q7` e `W1`) | 1m30s | 11m30s | Explicação técnica honesta: `Q7` reduziu E/S em 30,06%, mas caiu de `Batch Mode` (217 ms) para `Row Mode` (364 ms); `W1` sofreu +85,33% de escrita em 4 B+ Trees. |
| Pág. 12 (Seção 11) | **Demo Prática ao Vivo** | 4m30s | 16m00s | Executar `scripts/demo/01` a `04` lado a lado (`Ecommerce_Baseline` vs. `Ecommerce_Otimizado`) com *Actual Execution Plan* e `STATISTICS IO, TIME ON`. |
| Pág. 13 (Seção 12) | Conclusões e Perguntas | 1m30s | 17m30s | Regras práticas de indexação, limitações (`MAXDOP 1`, container) e abertura para arguição. |

## Perguntas Esperadas na Arguição (Respostas Rápidas)

1. **Por que usar SQL Server 2022 em Docker?**  
   Atende à restrição do edital (SGBD comercial, sem MySQL), entrega planos gráficos ricos (`ShowPlanXML`) e `SET STATISTICS IO, TIME ON` precisos, além de garantir reprodutibilidade idêntica em Windows e Ubuntu.
2. **Por que `OPTION (MAXDOP 1)`?**  
   Para isolar deterministicamente o efeito dos índices e algoritmos de acesso sem ruído de sincronização multi-thread em ambiente virtualizado/conteinerizado de 4 GB.
3. **Se `Q7` ficou mais lenta, o índice `IX_Pedidos_Status_Cov` falhou?**  
   Ele cumpriu o papel de reduzir E/S em 30,06% e eliminar concessão de memória do `Hash Match`, mas o otimizador subestimou o custo do `Stream Aggregate` em *Row Mode* frente ao `Hash Match` vetorizado em *Batch Mode* — evidenciando a importância de medir tempo além de leituras lógicas.
4. **O teste `W1` alterou a base durante os benchmarks?**  
   Não. Todo `INSERT` rodou dentro de `BEGIN TRANSACTION ... ROLLBACK TRANSACTION` após a coleta das mensagens, mantendo exatos 4.500.000 registros em `dbo.ItensPedido`.
