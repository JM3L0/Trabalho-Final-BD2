# Roteiro Rápido da Demonstração ao Vivo (~30s por cenário)

**Ferramenta:** `uv run python demo_interativo.py`  
**Caminho no menu:** `[1] Apresentação ao Vivo` → executar `[1]` a `[4]` (ou `[5]` para rodar em sequência)  
**Duração total:** ~2 min 10 s

---

## Abertura (~10s)

> "Vou rodar agora os quatro cenários principais ao vivo nas duas bases gêmeas de 6,25 milhões de linhas — à esquerda o Baseline, só com chaves primárias, e à direita a base Otimizada."

---

## `[1]` Q1 — Scan vs. Seek por `Email` (~30s)

* **Na tela:** `2.856 -> 6` páginas | `< 1 ms` | `Clustered Index Scan` vs. `Index Seek + Key Lookup`
* **Fala:**
  > "Aqui buscamos um único cliente pelo e-mail. No Baseline, como `Email` não tem índice, o plano faz um *Clustered Index Scan* e lê **2.856 páginas** da tabela inteira. Na base Otimizada, o índice `IX_Clientes_Email` transforma a operação em um *Index Seek* direto ao registro: cai para **6 páginas** e menos de **1 ms**. Reparem que ainda há um *Key Lookup* porque `Nome`, `Cidade` e `Estado` não estão no índice."

---

## `[2]` Q3 — Índice Composto: `Status` + `DataPedido` (~30s)

* **Na tela:** `8.090 -> 17` páginas | `Index Seek` puro em `IX_Pedidos_Status_Data` | `0` *Key Lookups*
* **Fala:**
  > "Na Q3 filtramos pedidos entregues em uma janela de sete dias. No Baseline, o banco varre todas as **8.090 páginas** de `Pedidos`. Na Otimizada, criamos o índice composto com `Status` primeiro — que é igualdade — e `DataPedido` depois — que é faixa. Assim o plano faz um único *Index Seek* em `IX_Pedidos_Status_Data`, lendo apenas **17 páginas**, já com zero *Key Lookups*."

---

## `[3]` Q4 — Covering Index com `INCLUDE` (~30s)

* **Na tela:** `8.090 -> 5` páginas (`-99,94%`) | `< 1 ms` | Estágio 2 (`1.296` pág., `422` lookups) $\rightarrow$ `Index Seek` puro
* **Fala:**
  > "A Q4 mostra na prática como eliminar o *Key Lookup*. Queremos `DataPedido` e `ValorTotal` de um intervalo de clientes. Sem índice, o Baseline lê **8.090 páginas**. Com um índice simples só em `ClienteID` — mostrado aqui como Estágio 2 — ele até acha rápido, mas faz **422 *Key Lookups***, somando **1.296 páginas**. Ao incluir `DataPedido` e `ValorTotal` no `INCLUDE`, o plano vira um *Index Seek* puro, em **5 páginas** e menos de **1 ms**."

---

## `[4]` W1 — Trade-off de Escrita (`10.000 INSERT`s + `ROLLBACK`) (~30s)

* **Na tela:** operador `Sequence` mantendo 4 B+ Trees | aumento de leituras/tempo | `[SEGURO] Pos-ROLLBACK: 4.500.000 linhas`
* **Fala:**
  > "Por fim, a W1 prova que índice não é gratuito. Inserimos 10 mil itens dentro de uma transação com `ROLLBACK` para não sujar a base. No Baseline, o SQL Server grava só na chave primária. Na Otimizada, aparece o operador `Sequence` atualizando **quatro árvores B+** ao mesmo tempo — a PK, duas FKs e o índice filtrado — elevando as leituras de I/O e o tempo de gravação. E aqui embaixo confirmamos que a base voltou intacta para **4,5 milhões** de linhas."

---

## Bônus para Arguição — Q7 (`Batch Mode` vs. `Row Mode`) (~25s)

* **Caminho no menu:** `[2] Consultas do Artigo` → `[7] Q7`
* **Na tela:** `8.090 -> 5.658` páginas (`-30,06%`) | `Batch` (Hash Match) vs. `Row` (Stream Aggregate) | Speedup `< 1,0x`
* **Fala:**
  > "Na Q7, o índice de cobertura reduziu as páginas lidas em **30%**, de 8.090 para 5.658. Mas o tempo subiu porque, no Baseline, o *Hash Match* rodou em **Batch Mode**, processando blocos de linhas; já o índice levou o otimizador a escolher *Stream Aggregate* em **Row Mode**, linha a linha, aumentando o custo de CPU."

---

## Contingência Rápida

* Se o Docker não subir, o `demo_interativo.py` entra automaticamente no **Plano B** (exibe os `.sqlplan` reais e estatísticas do experimento) sem quebrar a apresentação.
* Ao sair pelo `[0]`, o script derruba o container automaticamente (se foi subido por ele), preservando o volume `mssql_data`.
