# Guia Completo e Definitivo do Trabalho Final de Banco de Dados II

> **Para quem é este documento?**
> Este guia foi escrito **do zero absoluto** para explicar todo o projeto da nossa equipe na disciplina de **Banco de Dados II (UFPI — 2026.2, Prof. Dennis Sávio)**. Se você não participou da codificação ou ainda não entendeu o que são os índices, o que significam as siglas **Q1 a Q10 e W1**, como ler os resultados, como funciona o código ou o que falar nos slides e nos roteiros, **este documento explica tudo passo a passo, em linguagem simples e direta**.

---

## Sumário

1. [Parte 1 — O Que Estamos Fazendo? (Visão Geral do Zero)](#parte-1--o-que-estamos-fazendo-visão-geral-do-zero)
2. [Parte 2 — Dicionário Sem Mistério (Conceitos que Você Precisa Dominar)](#parte-2--dicionário-sem-mistério-conceitos-que-você-precisa-dominar)
3. [Parte 3 — Como Funciona o Nosso Experimento? (As Bases Gêmeas e os 9 Índices)](#parte-3--como-funciona-o-nosso-experimento-as-bases-gêmeas-e-os-9-índices)
4. [Parte 4 — O Que São Q1 a Q10 e W1? (Explicação Consulta por Consulta + Resultados)](#parte-4--o-que-são-q1-a-q10-e-w1-explicação-consulta-por-consulta--resultados)
5. [Parte 5 — Explicação Completa dos Resultados e Gráficos](#parte-5--explicação-completa-dos-resultados-e-gráficos)
6. [Parte 6 — Como Funciona o Código do Projeto? (Arquivo por Arquivo)](#parte-6--como-funciona-o-código-do-projeto-arquivo-por-arquivo)
7. [Parte 7 — Explicação dos Slides e dos Roteiros (Integrante por Integrante)](#parte-7--explicação-dos-slides-e-dos-roteiros-integrante-por-integrante)
8. [Parte 8 — Perguntas que o Professor Pode Fazer (E Como Responder)](#parte-8--perguntas-que-o-professor-pode-fazer-e-como-responder)

---

## Parte 1 — O Que Estamos Fazendo? (Visão Geral do Zero)

### 1.1. Qual é a tarefa do Trabalho Final?
O edital da disciplina ([Trabalho Final.pdf](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/Trabalho%20Final.pdf)) pediu um estudo prático e científico sobre **Indexação, Planos de Execução e Otimização de Consultas** em um Sistema Gerenciador de Banco de Dados (SGBD) comercial real (o edital proibiu MySQL).
A nota é dividida em duas entregas:
1. **Artigo Científico (7,0 pontos):** Escrito em LaTeX no formato da SBC com até 10 páginas ([paper/main.pdf](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/paper/main.pdf)).
2. **Apresentação Oral + Demonstração Prática (3,0 pontos):** Até 20 minutos para apresentar os slides ([slides/apresentacao.pdf](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/slides/apresentacao.pdf)) e mostrar as consultas rodando ao vivo no banco de dados.

### 1.2. Qual é o assunto central (em linguagem humana)?
Imagine que você tem uma lista telefônica ou um caderno com **6 milhões e 250 mil linhas** (que é o tamanho do banco de dados de E-Commerce que nós criamos).
- **Sem índice secundário (`Baseline`):** Se você pedir ao banco *"Encontre o cliente cujo e-mail é `cliente_125432@exemplo.com.br`"*, o banco de dados não sabe em qual página esse e-mail está, porque a tabela só está organizada pelo número do `ClienteID` (1, 2, 3...). Então o banco é obrigado a **ler todas as páginas da tabela do começo ao fim**. No banco de dados, isso se chama **Scan** (*Clustered Index Scan* ou *Table Scan*). É lento e gasta muita memória.
- **Com índice secundário (`Otimizado`):** Criar um índice em uma coluna é como criar um **índice remissivo (ou uma árvore de busca ordenada, chamada Árvore B+)** no final do livro. Quando você procura pelo e-mail, o banco olha nessa árvore, dá 3 ou 4 saltos certeiros e cai exatamente na página onde está aquele cliente. Isso se chama **Seek** (*Index Seek*).

### 1.3. Qual é a grande tese do nosso trabalho?
Muita gente acha que *"basta sair criando índices em tudo que o banco fica rápido"*. Nosso trabalho prova, com números reais no **Microsoft SQL Server 2022**, três verdades fundamentais:
1. **Quando bem projetados (combinados com consultas bem escritas), os índices reduzem as leituras de páginas em até 99,96% e deixam as consultas até mais de 424 vezes mais rápidas.**
2. **Só criar um índice simples muitas vezes não basta:** se a consulta pedir colunas que não estão no índice, o banco precisa ficar pulando do índice para a tabela principal (o chamado **Key Lookup**), ou se você escrever o `WHERE` do jeito errado (usando funções como `YEAR(Data)` ou `LIKE '%texto%'`), o banco simplesmente **ignora o índice**.
3. **Não existe "índice grátis" (Trade-offs):**
   - Na hora de **inserir dados novos (`INSERT`)**, cada índice extra na tabela precisa ser atualizado ao mesmo tempo, deixando a escrita mais pesada (provamos isso na carga **W1**, que aumentou o custo de leitura/escrita em **+85,33%** no cache quente e **+264,73%** no cache frio).
   - Em certas consultas analíticas que somam a tabela inteira (como a nossa consulta **Q7**), usar um índice pode até fazer o banco trocar um modo de processamento super moderno em lotes (**Batch Mode**) por um modo linha-a-linha mais antigo (**Row Mode**), deixando a consulta **mais lenta em tempo de CPU** mesmo lendo menos páginas!

---

## Parte 2 — Dicionário Sem Mistério (Conceitos que Você Precisa Dominar)

Antes de olhar os números, entenda estes termos que aparecem nos slides e nos roteiros:

### 2.1. Métricas que medimos no SQL Server
* **Página de Dados (8 KB):** O SQL Server não lê uma linha solta do disco ou da memória; ele guarda tudo em "blocos" fixos chamados **páginas de 8 Kilobytes (8 KB)**.
* **Leituras Lógicas (`logical reads`):** É a quantidade de páginas de 8 KB que o SQL Server precisou ler na **memória RAM (Buffer Pool)** para responder à consulta.
  * *Por que essa é a métrica mais importante do trabalho?* Porque o tempo em milissegundos pode oscilar se o Windows estiver ocupado em segundo plano, mas **a quantidade de páginas lidas (`logical reads`) é exata e determinística**: se uma consulta lê `8.090` páginas sem índice e passa a ler `5` páginas com índice, provamos matematicamente que o trabalho do banco caiu **99,94%**.
* **Leituras Físicas (`physical reads`) e `read-ahead reads`:** Quantas páginas de 8 KB precisaram ser buscadas no **SSD/disco físico** porque ainda não estavam na memória RAM.
* **Warm Cache (Cache Quente — $N = 30$):** É quando rodamos a consulta depois que os dados já subiram do SSD para a memória RAM (o estado normal de um servidor em produção). Medimos 30 vezes seguidas (após 2 rodadas de aquecimento descartadas).
* **Cold Cache (Cache Frio — $N = 10$):** É o "pior cenário": antes de cada execução, limpamos toda a memória RAM do SQL Server com os comandos `CHECKPOINT; DBCC DROPCLEANBUFFERS; DBCC FREEPROCCACHE;`, obrigando o banco a buscar tudo do SSD do zero e recompilar o plano. Medimos 10 vezes para cada consulta.
* **Speedup (Aceleração):** Quantas vezes a consulta ficou mais rápida:
  $$\text{Speedup} = \frac{\text{Tempo Mediano no Baseline}}{\text{Tempo Mediano no Otimizado}}$$
  * *Atenção:* Se o Speedup é **maior que 1** (ex.: `87,0x`), ficou 87 vezes mais rápido. Se o Speedup é **menor que 1** (ex.: `0,60x` na Q7 ou `0,46x` na W1), significa que ficou **mais lento**!
  * *Por que alguns Speedups têm o sinal `>` (ex.: `>424x (<1 ms)`)?* Porque o relógio interno do SQL Server (`SET STATISTICS TIME ON`) mede em milissegundos inteiros (`1 ms`). Quando a consulta otimizada é tão rápida que gasta menos de meio milissegundo (ex.: `0,2 ms`), o SQL Server mostra `0 ms`. Para não dividir por zero, assumimos de forma conservadora que ela demorou no máximo `< 1 ms`. Logo, de `424 ms` para `< 1 ms`, o ganho é de **pelo menos `>424x`**.

### 2.2. Estruturas de Índices no SQL Server
* **Árvore B+ (B+ Tree):** É a estrutura de dados de todos os índices tradicionais do SQL Server. Pense numa pirâmide: no topo está a **Raiz**, no meio os **Nós Intermediários** (que só guardam chaves e ponteiros, cabendo centenas por página de 8 KB) e na base estão as **Páginas Folha** (ligadas em ordem crescente e decrescente). Com apenas 2 a 4 níveis de altura, você acha qualquer linha entre milhões!
* **Índice Clusterizado (`PRIMARY KEY CLUSTERED`):** É a própria tabela! As páginas folha do índice clusterizado guardam a linha inteira com todas as colunas, fisicamente ordenadas pela chave primária (ex.: `PedidoID = 1, 2, 3...`). Só pode existir **1 índice clusterizado por tabela**.
* **Índice Não-Clusterizado (`NONCLUSTERED INDEX` — Índice Secundário):** É uma Árvore B+ separada, criada sobre outras colunas (ex.: `Email` ou `DataPedido`). Nas folhas dele, ele guarda a coluna indexada + o `ID` da chave primária para saber onde achar o resto da linha na tabela principal. Uma tabela pode ter vários índices secundários.
* **Key Lookup (A grande armadilha!):** Acontece quando você tem um índice secundário simples (ex.: apenas em `ClienteID`), mas o seu `SELECT` pede também `DataPedido` e `ValorTotal`. O banco acha o `ClienteID` no índice secundário, mas como `DataPedido` e `ValorTotal` não estão lá, ele precisa dar um "pulo" de volta na tabela principal (no índice clusterizado) para buscar essas colunas. Se a consulta retorna 422 linhas (caso da nossa **Q4**), o banco dá **422 pulos aleatórios**!
* **Covering Index / Índice de Cobertura (`INCLUDE`):** É a solução para o *Key Lookup*. Ao criar o índice em `ClienteID`, adicionamos `INCLUDE (DataPedido, ValorTotal)`. Isso copia essas colunas extras **apenas nas folhas** do índice secundário. Assim, o índice "cobre" 100% da consulta e o banco nem encosta na tabela principal!
* **Índice Composto:** Índice com duas ou mais colunas na chave, ex.: `(Status, DataPedido)`. **Regra de ouro:** coloca-se primeiro a coluna filtrada por **igualdade** (`Status = 'ENTREGUE'`) e depois a coluna filtrada por **faixa/intervalo** (`DataPedido >= ...`). Assim, todos os pedidos entregues daquela semana ficam juntinhos (contíguos) na folha da árvore.
* **Índice Filtrado (`WHERE`):** Um índice que só indexa uma parte da tabela (ex.: `WHERE Desconto >= 10.00`). No nosso banco, apenas ~20% dos itens têm desconto alto, então o índice fica 80% menor e pesa muito menos nas inserções.

### 2.3. Sargabilidade e Operadores do Plano de Execução
* **Consulta Sargable (*Search ARGument ABLE*):** Uma consulta é *sargable* quando o otimizador consegue usar a condição do `WHERE` para navegar na Árvore B+ (*Index Seek*).
  * **NÃO é sargable:** `WHERE YEAR(DataPedido) = 2025` (o banco precisa calcular `YEAR()` nas 1,5 milhão de linhas uma por uma) ou `WHERE Nome LIKE '%Notebook%'` (o `%` no começo impede usar a ordem alfabética).
  * **É sargable:** `WHERE DataPedido >= '2025-01-01' AND DataPedido < '2026-01-01'` e `WHERE Nome LIKE 'Notebook%'`.
* **Operadores Físicos (as "caixinhas" que aparecem no gráfico do Plano de Execução):**
  * **`Clustered Index Scan`:** Leu a tabela inteira do início ao fim ($O(N)$). Ruim para buscas seletivas.
  * **`Index Seek` / `Clustered Index Seek`:** Navegou direto pela Árvore B+ até os dados desejados ($O(\log_m N)$). Excelente!
  * **`Sort` / `Top N Sort`:** O banco precisou gastar memória e CPU para colocar as linhas em ordem porque elas não vieram ordenadas de um índice.
  * **`Nested Loops` (Loops Aninhados):** Operador de junção (`JOIN`) ideal quando um lado tem poucas linhas e o outro lado tem um índice rápido para buscar cada correspondência.
  * **`Merge Join` (Junção por Intercalação):** Operador de `JOIN` super rápido quando as duas tabelas já vêm ordenadas pela coluna de junção graças aos índices!
  * **`Hash Match` (Junção ou Agregação por Hash):** Quando não há índices adequados (ou o volume é gigantesco e desordenado), o banco constrói uma tabela Hash na memória RAM. Gasta bastante memória e CPU.
  * **`Stream Aggregate`:** Agrupamento (`GROUP BY`) onde as linhas já vêm ordenadas pelo índice; o banco só vai somando enquanto o grupo não muda, sem gastar memória com tabela Hash.
  * **`Batch Mode on Rowstore` vs. `Row Mode`:** No SQL Server 2022, operadores pesados como `Hash Match` em tabelas grandes podem rodar em **Batch Mode** (processando pacotes vetorizados de até ~900 linhas de uma vez na CPU), enquanto operadores como `Stream Aggregate` sobre índices B+ tradicionais rodam em **Row Mode** (chamando funções internamente linha por linha).
* **Estatística e Isolamento:**
  * **`OPTION (MAXDOP 1)`:** Força o SQL Server a usar apenas **1 núcleo de CPU (1 thread)** por consulta. Fizemos isso para que o paralelismo do Docker não causasse variações aleatórias de tempo entre uma rodada e outra.
  * **Shapiro-Wilk, t-Student e Wilcoxon:** O script Python testa se as diferenças de tempo seguem uma distribuição normal (teste de *Shapiro-Wilk*). Se sim, usa o **Teste t de Student pareado**; se não (que é o mais comum em tempos de banco de dados), usa o **Teste de Wilcoxon pareado**. Ambos geram o **$p$-valor ($p$-value)**: quando $p < 0,05$ (no nosso caso, deu $p < 0,0001$ em todas as leituras!), fica provado cientificamente que a diferença não foi sorte ou acaso.

---

## Parte 3 — Como Funciona o Nosso Experimento? (As Bases Gêmeas e os 9 Índices)

### 3.1. O Cenário: E-Commerce B2C com 6.250.000 Linhas
Criamos um gerador em Python ([scripts/generate_data.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/generate_data.py)) com semente fixa (`SEED = 42`). Isso significa que qualquer pessoa que rodar o código em qualquer computador vai gerar **exatamente os mesmos dados, centavo por centavo, data por data**.

O banco modela uma loja virtual com **4 tabelas**:

| Tabela | Quantidade de Linhas | Chave Primária (Clusterizada) | Colunas Principais e Detalhes |
| :--- | ---: | :--- | :--- |
| **`dbo.Clientes`** | **200.000** | `PK_Clientes (ClienteID)` | `ClienteID`, `Nome` (`NVARCHAR`), `Email` (`VARCHAR`), `Cidade`, `Estado`, `DataCadastro`. *(Nota: apenas os clientes de 1 a 190.000 fazem pedidos; exatamente 10.000 clientes nunca compraram nada, para testarmos a Q10!)* |
| **`dbo.Produtos`** | **50.000** | `PK_Produtos (ProdutoID)` | `ProdutoID`, `Nome` (`NVARCHAR(150)`), `Categoria`, `Preco`, `Estoque`. |
| **`dbo.Pedidos`** | **1.500.000** | `PK_Pedidos (PedidoID)` | `PedidoID`, `ClienteID` (FK), `DataPedido` (`DATETIME2(0)` entre 2022 e out/2026), `Status` (`ENTREGUE` 55%, `PAGO` 15%, `ENVIADO` 12%, `PENDENTE` 8%, `CANCELADO` 7%, `DEVOLVIDO` 3%), `ValorTotal`. |
| **`dbo.ItensPedido`** | **4.500.000** | `PK_ItensPedido (ItemPedidoID)` | `ItemPedidoID`, `PedidoID` (FK), `ProdutoID` (FK), `Quantidade` (1 a 5), `PrecoUnitario`, `Desconto` (`0%`, `5%`, `10%` ou `15%` — sendo que `10%` e `15%` somam 20% da tabela). |
| **TOTAL** | **6.250.000** | **4 PKs Clusterizadas** | **~400 MB alocados no SQL Server (~245 MB em arquivos CSV)** |

### 3.2. A Metodologia das "Bases Gêmeas"
Em vez de ter um banco só e ficar criando e apagando índices na hora da apresentação (o que demoraria minutos e mudaria as estatísticas do banco), nós criamos **duas bases de dados gêmeas dentro do mesmo container SQL Server 2022**:

1. **`Ecommerce_Baseline` (Grupo de Controle):**
   - Recebe a carga dos 6,25 milhões de registros via `BULK INSERT`.
   - Possui **APENAS as 4 chaves primárias clusterizadas (`PK`)** e **ZERO índices secundários**.
2. **`Ecommerce_Otimizado` (Grupo Experimental):**
   - É criada tirando um `BACKUP DATABASE` completo da `Ecommerce_Baseline` e fazendo `RESTORE DATABASE` com outro nome ([scripts/sql/03_backup_and_clone.sql](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/sql/03_backup_and_clone.sql)). Isso garante que as duas bases comecem **100% idênticas bit a bit**.
   - Em seguida, aplicamos **9 índices secundários estratégicos** somente nela ([scripts/sql/04_create_indexes_optimized.sql](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/sql/04_create_indexes_optimized.sql)) e atualizamos as estatísticas com `EXEC sp_updatestats`.

### 3.3. Os 9 Índices Secundários Criados na Base Otimizada
Aqui está a lista exata dos 9 índices que existem em `Ecommerce_Otimizado` e para que cada um serve:

| # | Nome do Índice | Tabela | Definição (`Chave` + `INCLUDE` / `WHERE`) | Tipo de Índice | Quais Consultas Ele Atende? |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **1** | `IX_Clientes_Email` | `Clientes` | `(Email)` | Simples | **Q1** (busca pontual por e-mail) |
| **2** | `IX_Produtos_Nome` | `Produtos` | `(Nome) INCLUDE (Categoria, Preco)` | Cobertura (*Covering*) | **Q8** (busca textual por prefixo `LIKE N'Notebook%'`) |
| **3** | `IX_Pedidos_DataPedido` | `Pedidos` | `(DataPedido) INCLUDE (ClienteID, Status, ValorTotal)` | Cobertura (*Covering*) | **Q2** (faixa de datas), **Q6** (`TOP 50` mais recentes sem `Sort`) e **Q9** (pedidos de 2025) |
| **4** | `IX_Pedidos_Status_Data` | `Pedidos` | `(Status, DataPedido)` | Composto (Igualdade + Faixa) | **Q3** (pedidos `ENTREGUE` em uma semana específica) |
| **5** | `IX_Pedidos_ClienteID_Cov` | `Pedidos` | `(ClienteID) INCLUDE (DataPedido, ValorTotal)` | Cobertura (*Covering*) | **Q4** (elimina 422 *Key Lookups*), **Q5** (join com Clientes) e **Q10** (clientes sem pedido) |
| **6** | `IX_Pedidos_Status_Cov` | `Pedidos` | `(Status) INCLUDE (ValorTotal)` | Cobertura (*Covering*) | **Q7** (agregação `GROUP BY Status` com *Stream Aggregate*) |
| **7** | `IX_ItensPedido_PedidoID` | `ItensPedido` | `(PedidoID) INCLUDE (ProdutoID, Quantidade, PrecoUnitario)` | Cobertura (*Covering*) | **Q5** (join rápido de pedidos com seus itens) + cobrado na escrita **W1** |
| **8** | `IX_ItensPedido_ProdutoID` | `ItensPedido` | `(ProdutoID)` | Simples em FK | Indexação de chave estrangeira de produto + cobrado na escrita **W1** |
| **9** | `IX_ItensPedido_Desconto_Alto` | `ItensPedido` | `(ProdutoID, Desconto) WHERE Desconto >= 10.00` | Filtrado (*Filtered Index*) | Indexa apenas ~20% da tabela (901.180 linhas) + cobrado parcialmente na escrita **W1** |

---

## Parte 4 — O Que São Q1 a Q10 e W1? (Explicação Consulta por Consulta + Resultados)

Nosso benchmark é composto por **11 cargas de trabalho**:
- **Q1 até Q10:** São **10 consultas de leitura (`SELECT`)**, onde cada letra **"Q"** significa *Query* (Consulta).
- **W1:** É **1 operação de escrita em massa (`INSERT`)**, onde a letra **"W"** significa *Write* (Escrita).

> **Detalhe importante:** Nas consultas **Q1, Q2, Q3, Q4, Q5, Q6, Q7 e W1**, o código SQL executado no `Ecommerce_Baseline` e no `Ecommerce_Otimizado` é **exatamente o mesmo** (o ganho vem puramente dos índices criados!). Já nas consultas **Q8, Q9 e Q10**, além do índice, nós também mostramos a **reescrita do SQL** (tirando armadilhas que impediam o uso de índices).

Abaixo está a explicação completa de cada uma delas!

---

### 🔹 Q1 — Busca Pontual de Cliente por E-mail (*Scan vs. Seek*)
* **O que ela faz:** Procura os dados de **1 único cliente** (entre 200.000 clientes) pelo endereço de e-mail exato.
* **Código SQL (idêntico nas duas bases):**
  ```sql
  SELECT ClienteID, Nome, Email, Cidade, Estado
  FROM dbo.Clientes
  WHERE Email = 'cliente_125432@exemplo.com.br'
  OPTION (MAXDOP 1);
  ```
* **Retorno:** `1 linha`.
* **O que acontece no Baseline (Sem índice):** Como `Clientes` só tem índice no `ClienteID`, o SQL Server faz um **`Clustered Index Scan (PK_Clientes)`**, lendo todas as 200.000 linhas da tabela para achar 1 pessoa.
* **O que acontece no Otimizado (Com índice):** O SQL Server usa o índice `IX_Clientes_Email` para fazer um **`Index Seek`** direto no e-mail e depois faz **1 único `Key Lookup`** na `PK_Clientes` (via `Nested Loops`) para pegar `Nome`, `Cidade` e `Estado`. Como é só 1 linha, fazer 1 *Key Lookup* é instantâneo!
* **Resultado Medido (Warm Cache $N=30$):**
  * **Leituras Lógicas:** Caiu de **2.856 páginas** para **6 páginas** (**redução de 99,79%**).
  * **Tempo Mediano:** Caiu de **15,0 ms** para **< 1 ms (0,0 ms)** (**Speedup > 15x**).
  * **Cold Cache ($N=10$):** Caiu de **44,0 ms** para **3,5 ms** (**Speedup 12,6x**).

---

### 🔹 Q2 — Filtro de Pedidos por Faixa de Datas (*Range Scan vs. Range Seek*)
* **O que ela faz:** Busca o `PedidoID` e a `DataPedido` de todos os pedidos feitos em uma janela de 1 semana (de `01/06/2025` a `08/06/2025`) dentro de uma tabela de 1.500.000 pedidos.
* **Código SQL (idêntico nas duas bases):**
  ```sql
  SELECT PedidoID, DataPedido
  FROM dbo.Pedidos
  WHERE DataPedido >= '2025-06-01' AND DataPedido < '2025-06-08'
  OPTION (MAXDOP 1);
  ```
* **Retorno:** `6.028 linhas`.
* **O que acontece no Baseline:** Faz **`Clustered Index Scan (PK_Pedidos)`**, lendo os 1.500.000 pedidos inteiros.
* **O que acontece no Otimizado:** Faz **`Index Seek (IX_Pedidos_DataPedido)`** navegando direto para o dia `2025-06-01` e lendo sequencialmente as folhas até `2025-06-08`. Como `PedidoID` é a chave clusterizada da tabela, ela já está automaticamente guardada dentro de qualquer índice secundário! Logo, não precisa de *Key Lookup*.
* **Resultado Medido (Warm Cache $N=30$):**
  * **Leituras Lógicas:** Caiu de **8.090 páginas** para **34 páginas** (**redução de 99,58%**).
  * **Tempo Mediano:** Caiu de **104,5 ms** para **1,5 ms** (**Speedup de 69,7x**).
  * **Cold Cache ($N=10$):** Caiu de **281,5 ms** para **6,0 ms** (**Speedup de 46,9x**).

---

### 🔹 Q3 — Filtro Composto: Igualdade (`Status`) + Faixa (`DataPedido`)
* **O que ela faz:** Busca os pedidos com `Status = 'ENTREGUE'` realizados na última semana de outubro de 2026 (`25/10/2026` a `01/11/2026`).
* **Código SQL (idêntico nas duas bases):**
  ```sql
  SELECT PedidoID, Status, DataPedido
  FROM dbo.Pedidos
  WHERE Status = 'ENTREGUE'
    AND DataPedido >= '2026-10-25' AND DataPedido < '2026-11-01'
  OPTION (MAXDOP 1);
  ```
* **Retorno:** `3.198 linhas`.
* **Por que essa consulta é importante?** Ela ensina como criar um **Índice Composto (`IX_Pedidos_Status_Data (Status, DataPedido)`)**. Como `Status` tem filtro de **igualdade (`=`)**, ele vem **primeiro** na chave do índice; como `DataPedido` tem filtro de **intervalo (`>=` e `<`)**, ele vem **depois**. Assim, dentro da fatia `'ENTREGUE'`, as datas estão perfeitamente em ordem cronológica!
* **O que acontece no Baseline vs. Otimizado:** Sai de um **`Clustered Index Scan`** de toda a tabela `Pedidos` (8.090 páginas) para um **`Index Seek` puro** no índice composto (sem *Key Lookup*, pois `PedidoID`, `Status` e `DataPedido` estão todos no índice).
* **Resultado Medido (Warm Cache $N=30$):**
  * **Leituras Lógicas:** Caiu de **8.090 páginas** para **17 páginas** (**redução de 99,79%**).
  * **Tempo Mediano:** Caiu de **87,0 ms** para **1,0 ms** (**Speedup de 87,0x**).
  * **Cold Cache ($N=10$):** Caiu de **246,5 ms** para **6,5 ms** (**Speedup de 37,9x**).

---

### 🔹 Q4 — O Estudo de Caso em 3 Estágios: A Armadilha do *Key Lookup* e a Solução com `INCLUDE`
* **O que ela faz:** Busca `ClienteID`, `DataPedido` e `ValorTotal` dos pedidos de uma faixa de 51 clientes (`ClienteID BETWEEN 1000 AND 1050`).
* **Código SQL (idêntico nos 3 estágios):**
  ```sql
  SELECT ClienteID, DataPedido, ValorTotal
  FROM dbo.Pedidos
  WHERE ClienteID BETWEEN 1000 AND 1050
  OPTION (MAXDOP 1);
  ```
* **Retorno:** `422 linhas`.
* **Por que Q4 tem um gráfico próprio nos slides (Estudo em 3 Estágios)?** Porque nós testamos **3 situações diferentes** para mostrar na prática o que é o *Key Lookup*:
  1. **Estágio 1 — Baseline (Sem índice secundário):** O banco faz **`Clustered Index Scan`** na tabela `Pedidos` inteira. Lê **8.090 páginas** e gasta **111,0 ms**.
  2. **Estágio 2 — Intermediário (Com índice simples `IX_Pedidos_ClienteID (ClienteID)` sem `INCLUDE`):** O banco usa o índice para achar os 422 pedidos rapidamente (gastando só 4 páginas no índice), **MAS** como o índice simples não tem as colunas `DataPedido` e `ValorTotal`, o banco precisa executar um **`Key Lookup` 422 vezes** (uma para cada linha encontrada!) na tabela principal via `Nested Loops`. Resultado: os 422 pulos consomem **99,6% do custo do plano** e geram **1.296 leituras lógicas** (plano salvo em [q4_intermediate_lookup.sqlplan](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/results/plans/optimized/q4_intermediate_lookup.sqlplan)).
  3. **Estágio 3 — Otimizado Final (Com Índice de Cobertura `IX_Pedidos_ClienteID_Cov (ClienteID) INCLUDE (DataPedido, ValorTotal)`):** Agora `DataPedido` e `ValorTotal` estão guardados direto na folha do índice! O operador *Key Lookup* desaparece completamente, sobrando um único **`Index Seek`**.
* **Resultado Medido (Warm Cache $N=30$):**
  * **Leituras Lógicas:** **8.090 páginas** (Baseline) $\rightarrow$ **1.296 páginas** (Intermediário com Lookup) $\rightarrow$ **5 páginas** (Otimizado com `INCLUDE`). Redução de **99,94%** sobre o Baseline e **99,61%** sobre o índice simples!
  * **Tempo Mediano:** Caiu de **111,0 ms** para **< 1 ms (0,0 ms)** (**Speedup > 111x**). Em Cold Cache, caiu de **194,0 ms** para **2,0 ms** (**97,0x**).

---

### 🔹 Q5 — Junção (`JOIN`) de 3 Tabelas: `Clientes` + `Pedidos` + `ItensPedido`
* **O que ela faz:** Monta um relatório detalhado juntando dados do cliente, seus pedidos e os itens de cada pedido para os clientes de ID `1000` a `1200`.
* **Código SQL (idêntico nas duas bases):**
  ```sql
  SELECT c.ClienteID, c.Nome, p.PedidoID, p.DataPedido,
         i.ProdutoID, i.Quantidade, i.PrecoUnitario
  FROM dbo.Clientes c
  INNER JOIN dbo.Pedidos p ON p.ClienteID = c.ClienteID
  INNER JOIN dbo.ItensPedido i ON i.PedidoID = p.PedidoID
  WHERE c.ClienteID BETWEEN 1000 AND 1200
  OPTION (MAXDOP 1);
  ```
* **Retorno:** `4.965 linhas`.
* **O que acontece no Baseline:** Sem índices nas chaves estrangeiras (`Pedidos.ClienteID` e `ItensPedido.PedidoID`), o SQL Server é obrigado a varrer as tabelas gigantes (`8.090` páginas em `Pedidos` + `20.721` páginas em `ItensPedido`) e juntar tudo na memória usando dois operadores **`Hash Match [Inner Join]`** pesadíssimos.
* **O que acontece no Otimizado:** Com os índices de cobertura nas FKs (`IX_Pedidos_ClienteID_Cov` e `IX_ItensPedido_PedidoID`), o banco elimina todos os *Scans* e todos os *Hash Joins*! Ele junta `Clientes` e `Pedidos` com um **`Merge Join`** super leve (lendo só 7 páginas de `Clientes` e 10 páginas de `Pedidos`, já que ambos estão ordenados por `ClienteID`) e depois busca os itens de cada pedido com **`Nested Loops` + `Index Seek`**!
* **Resultado Medido (Warm Cache $N=30$):**
  * **Leituras Lógicas:** Caiu de **28.818 páginas** para **5.295 páginas** (**redução de 81,63%**).
  * **Tempo Mediano:** Caiu de **450,0 ms** para **12,0 ms** (**Speedup de 37,5x**).
  * **Cold Cache ($N=10$):** Caiu de **1.027,5 ms (mais de 1 segundo!)** para **237,5 ms** (**Speedup de 4,33x**).

---

### 🔹 Q6 — Paginação dos 50 Pedidos Mais Recentes (`TOP 50 ... ORDER BY DataPedido DESC`)
* **O que ela faz:** Mostra na tela os 50 últimos pedidos da loja em ordem decrescente de data (típico painel de administração).
* **Código SQL (idêntico nas duas bases):**
  ```sql
  SELECT TOP 50 PedidoID, ClienteID, DataPedido, Status, ValorTotal
  FROM dbo.Pedidos
  WHERE ... -- (sem WHERE, direto na tabela toda)
  ORDER BY DataPedido DESC
  OPTION (MAXDOP 1);
  ```
* **Retorno:** `50 linhas`.
* **O que acontece no Baseline:** Como os pedidos estão ordenados por `PedidoID` e não por `DataPedido`, para descobrir quais são os 50 mais recentes o banco precisa ler os **1.500.000 pedidos inteiros (`Clustered Index Scan`, 8.090 páginas)** e passar tudo por um operador **`Sort [TopN Sort]`** caríssimo em CPU!
* **O que acontece no Otimizado:** O índice `IX_Pedidos_DataPedido` já guarda todos os pedidos em ordem de data e já inclui `ClienteID, Status, ValorTotal` na folha! Então o SQL Server faz uma leitura de trás para frente (**`Backward Scan`**) na última página do índice, pega as 50 primeiras linhas do final e **para imediatamente**, eliminando o operador `Sort`!
* **Resultado Medido (Warm Cache $N=30$) — O Maior Ganho do Trabalho:**
  * **Leituras Lógicas:** Caiu de **8.090 páginas** para apenas **3 páginas** (**redução de 99,96%**!).
  * **Tempo Mediano:** Caiu de **424,0 ms** para **< 1 ms (0,0 ms)** (**Speedup > 424x**!).
  * **Cold Cache ($N=10$):** Caiu de **772,0 ms** para **2,0 ms** (**Speedup de 386,0x**).

---

### 🔹 Q7 — O Grande Contra-Exemplo (Trade-off): Agregação de Faturamento por `Status`
* **O que ela faz:** Calcula a quantidade de pedidos e a soma de faturamento (`SUM(ValorTotal)`) para cada um dos 6 status da tabela `Pedidos` (varrendo todos os 1.500.000 pedidos, pois não tem `WHERE`).
* **Código SQL (idêntico nas duas bases):**
  ```sql
  SELECT Status, COUNT(*) AS QtdPedidos, SUM(ValorTotal) AS FaturamentoTotal
  FROM dbo.Pedidos
  GROUP BY Status
  OPTION (MAXDOP 1);
  ```
* **Retorno:** `6 linhas` (os 6 status: `ENTREGUE`, `PAGO`, `ENVIADO`, `PENDENTE`, `CANCELADO`, `DEVOLVIDO`).
* **O que acontece no Baseline:** O banco lê a tabela `Pedidos` inteira (`Clustered Index Scan`, **8.090 páginas**) e agrupa usando **`Hash Match [Aggregate]`**.
* **O que acontece no Otimizado:** Criamos o índice cobridor `IX_Pedidos_Status_Cov (Status) INCLUDE (ValorTotal)`. Como esse índice só tem 2 colunas em vez das 5 da tabela, ele é mais estreito: o banco lê apenas **5.658 páginas (redução de 30,06% em E/S)**. Além disso, como o índice já está ordenado por `Status`, o otimizador estima que o custo cairá pela metade (de `12,64` para `6,73`) e troca o `Hash Match` pelo operador **`Stream Aggregate`** (que não gasta memória RAM com tabela hash).
* **O PARADOXO (Por que o tempo piorou de 217 ms para 364 ms?!):**
  * Olhando o arquivo XML do plano real (`ShowPlanXML`), descobrimos o motivo exato: no **Baseline**, ao ver uma varredura de 1,5 milhão de linhas com `Hash Match`, o SQL Server 2022 ativou um recurso moderno chamado **`Batch Mode on Rowstore`**, que processa vetores de até 900 linhas de uma só vez nos registradores da CPU (**217,0 ms**).
  * Já no **Otimizado**, o operador `Stream Aggregate` sobre índice B+ tradicional não suporta *Batch Mode* e rodou no modo clássico **`Row Mode`** (processando linha por linha, 1.500.000 vezes, em 1 única thread por causa do `MAXDOP 1`). O custo de CPU de processar linha por linha foi maior do que a economia de 30% de páginas em memória, subindo o tempo para **364,0 ms** (**Speedup de 0,60x**, ou seja, 67,7% mais lento)!
  * *Por que esse resultado é excelente para a nossa nota?* Porque mostra maturidade científica! Prova que nós não "maquiamos" dados e que sabemos explicar que **reduzir leitura de páginas nem sempre reduz tempo de CPU** devido aos modos de execução internos do SQL Server 2022.

---

### 🔹 Q8 — Sargabilidade em Texto: `LIKE '%Notebook%'` vs. `LIKE 'Notebook%'`
* **O que ela faz:** Busca produtos da linha Notebook na tabela `Produtos` (50.000 linhas).
* **Aqui o SQL muda entre Baseline e Otimizado!**
  * **SQL Baseline (Não-Sargable — curinga `%` no início):**
    ```sql
    SELECT ProdutoID, Nome, Categoria, Preco
    FROM dbo.Produtos
    WHERE Nome LIKE N'%Notebook%'
    OPTION (MAXDOP 1);
    ```
  * **SQL Otimizado (Sargable — busca por prefixo sem `%` no início):**
    ```sql
    SELECT ProdutoID, Nome, Categoria, Preco
    FROM dbo.Produtos
    WHERE Nome LIKE N'Notebook%'
    OPTION (MAXDOP 1);
    ```
* **Retorno:** `2.002 linhas` (exatamente as mesmas 2.002 linhas nos dois casos!).
* **Por que funciona e dois detalhes técnicos importantíssimos:**
  1. Quando você escreve `LIKE N'%Notebook%'`, a palavra pode estar no meio do texto; a ordem alfabética do índice `IX_Produtos_Nome` não serve para nada, forçando um **`Clustered Index Scan`** (637 páginas, 114,0 ms). Ao mudar para prefixo `LIKE N'Notebook%'`, o banco vai direto na letra `"N"` da Árvore B+ (**`Index Seek`**, 28 páginas, 1,0 ms).
  2. **Ressalva semântica (fale isso na apresentação!):** Mudar de `'%termo%'` para `'termo%'` só retorna o mesmo resultado quando os nomes dos produtos seguem uma padronização onde a categoria vem no início do nome (`"Notebook Pro Serie..."`). Se fosse busca de palavra solta no meio de uma descrição livre, um índice B+ não resolveria (seria necessário um *Full-Text Index*).
  3. **Por que tem a letra `N` antes das aspas (`N'Notebook%'`)?** Porque a coluna `Nome` é do tipo `NVARCHAR(150)` (Unicode). Se você esquecer o `N`, o SQL Server trata o texto como `VARCHAR` e faz uma conversão implícita (`CONVERT_IMPLICIT`) que estraga a performance do índice!
* **Resultado Medido (Warm Cache $N=30$):**
  * **Leituras Lógicas:** Caiu de **637 páginas** para **28 páginas** (**redução de 95,60%**).
  * **Tempo Mediano:** Caiu de **114,0 ms** para **1,0 ms** (**Speedup de 114,0x**).

---

### 🔹 Q9 — Sargabilidade em Datas: Função `YEAR(DataPedido)` vs. Intervalo Semiaberto
* **O que ela faz:** Conta quantos pedidos foram feitos no ano de 2025 (`COUNT(*)`).
* **Aqui o SQL também muda entre Baseline e Otimizado!**
  * **SQL Baseline (Não-Sargable — coluna presa dentro da função `YEAR()`):**
    ```sql
    SELECT COUNT(*) AS TotalPedidos2025
    FROM dbo.Pedidos
    WHERE YEAR(DataPedido) = 2025
    OPTION (MAXDOP 1);
    ```
  * **SQL Otimizado (Sargable — coluna isolada em intervalo semiaberto):**
    ```sql
    SELECT COUNT(*) AS TotalPedidos2025
    FROM dbo.Pedidos
    WHERE DataPedido >= '2025-01-01' AND DataPedido < '2026-01-01'
    OPTION (MAXDOP 1);
    ```
* **Retorno:** `1 linha` (contendo o total de pedidos de 2025).
* **Por que funciona?** No SQL Server, o otimizador não "desmonta" a função `YEAR(DataPedido)` sozinho: ele lê as 1.500.000 linhas (`Clustered Index Scan`, 8.090 páginas) aplicando a função data por data. Quando reescrevemos como `DataPedido >= '2025-01-01' AND DataPedido < '2026-01-01'`, deixamos a coluna limpa! O banco faz um **`Index Seek`** apenas na fatia do ano de 2025 dentro do índice `IX_Pedidos_DataPedido` e conta as entradas com `Stream Aggregate`.
  * *Dica:* Usamos `< '2026-01-01'` (intervalo semiaberto) em vez de `BETWEEN '2025-01-01' AND '2025-12-31'` porque `DataPedido` tem hora/minuto/segundo (`DATETIME2(0)`), e `BETWEEN '2025-12-31'` perderia os pedidos feitos no dia 31/12 depois da meia-noite!
* **Resultado Medido (Warm Cache $N=30$):**
  * **Leituras Lógicas:** Caiu de **8.090 páginas** para **1.565 páginas** (**redução de 80,66%**).
  * **Tempo Mediano:** Caiu de **226,0 ms** para **26,0 ms** (**Speedup de 8,69x**).

---

### 🔹 Q10 — Otimização Lógica: Subconsulta Correlacionada Agregada vs. `NOT EXISTS`
* **O que ela faz:** Encontra todos os clientes que **nunca fizeram nenhum pedido** na loja.
* **Aqui o SQL também muda entre Baseline e Otimizado!**
  * **SQL Baseline (Subconsulta correlacionada com `MAX(DataPedido) IS NULL`):**
    ```sql
    SELECT c.ClienteID, c.Nome, c.Email
    FROM dbo.Clientes c
    WHERE (SELECT MAX(p.DataPedido) FROM dbo.Pedidos p WHERE p.ClienteID = c.ClienteID) IS NULL
    OPTION (MAXDOP 1);
    ```
  * **SQL Otimizado (Antijunção semântica com `NOT EXISTS`):**
    ```sql
    SELECT c.ClienteID, c.Nome, c.Email
    FROM dbo.Clientes c
    WHERE NOT EXISTS (SELECT 1 FROM dbo.Pedidos p WHERE p.ClienteID = c.ClienteID)
    OPTION (MAXDOP 1);
    ```
* **Retorno:** `10.060 linhas` (os clientes sem pedidos).
* **O que muda no Plano de Execução:**
  * No **Baseline**, pedir `MAX(p.DataPedido) IS NULL` obriga o banco a varrer todos os 1.500.000 pedidos, calcular o `MAX` de todos os clientes via **`Hash Match [Aggregate]`**, fazer um **`Hash Match [Right Outer Join]`** com `Clientes` e depois filtrar quem ficou nulo (`Filter`). Lê **10.946 páginas** e gasta **370,5 ms**.
  * No **Otimizado**, o `NOT EXISTS` avisa ao otimizador que **basta existir 1 pedido para descartar o cliente** (sem precisar achar a maior data!). Como `Clientes` já está ordenado por `ClienteID` e `Pedidos` tem o índice `IX_Pedidos_ClienteID_Cov` também ordenado por `ClienteID`, o banco aplica um **`Merge Join [Left Anti Semi Join]`** direto, eliminando as duas tabelas Hash!
* **Resultado Medido (Warm Cache $N=30$):**
  * **Leituras Lógicas:** Caiu de **10.946 páginas** para **8.252 páginas** (**redução de 24,61%**).
  * **Tempo Mediano:** Caiu de **370,5 ms** para **219,5 ms** (**Speedup de 1,69x**).

---

### 🔸 W1 — O Custo dos Índices na Escrita: Inserção em Lote de 10.000 Itens (`INSERT`)
* **O que ela faz:** Simula uma carga pesada de escrita inserindo **10.000 novas linhas** de uma vez na tabela `dbo.ItensPedido` (que já tem 4.500.000 linhas).
* **Código SQL (idêntico nas duas bases, rodando dentro de transação com `ROLLBACK`):**
  ```sql
  BEGIN TRANSACTION;
  INSERT INTO dbo.ItensPedido (ItemPedidoID, PedidoID, ProdutoID, Quantidade, PrecoUnitario, Desconto)
  SELECT ItemPedidoID + 4500000, PedidoID, ProdutoID, Quantidade, PrecoUnitario, Desconto
  FROM dbo.ItensPedido
  WHERE ItemPedidoID <= 10000
  OPTION (MAXDOP 1);
  ROLLBACK TRANSACTION;
  ```
* **Por que usamos `BEGIN TRANSACTION ... ROLLBACK TRANSACTION`?**
  Porque nós medimos as estatísticas (`SET STATISTICS IO, TIME ON`) **imediatamente após o `INSERT`** (portanto, o SQL Server realmente fez todo o trabalho pesado de gravar nas árvores B+ e checar as chaves estrangeiras!), e logo depois damos `ROLLBACK` para desfazer a inserção. Assim, a tabela continua tendo exatamente **4.500.000 linhas** para a próxima rodada do benchmark!
* **O que acontece no Baseline vs. Otimizado (Amplificação de Escrita):**
  * No **Baseline**, a tabela `ItensPedido` só tem a chave primária (`PK_ItensPedido`). O banco só faz **1 `Clustered Index Insert`**.
  * No **Otimizado**, a tabela `ItensPedido` tem **3 índices secundários extras** (`IX_ItensPedido_PedidoID`, `IX_ItensPedido_ProdutoID` e o índice filtrado `IX_ItensPedido_Desconto_Alto`). No plano de execução aparece um operador **`Sequence`** que obriga o banco a ordenar e atualizar **4 Árvores B+ diferentes** na mesma transação (sendo que o índice filtrado grava apenas as `1.964` linhas entre as `10.000` que têm `Desconto >= 10.00`).
* **Resultado Medido:**
  * **Em Warm Cache ($N=30$):** As leituras lógicas subiram de **97.154 páginas** para **180.057 páginas** (**um aumento de +85,33% de E/S!**). O tempo mediano passou de **384,0 ms** para **404,0 ms** (**Speedup 0,95x**, com altíssima oscilação/desvio padrão de `853,2 ms` por causa de *page splits* e checkpoint; como oscila muito em memória, o $p$-valor em Warm deu `0,1294`).
  * **Em Cold Cache ($N=10$):** Quando a memória está limpa, o peso de carregar e atualizar 4 árvores B+ do disco aparece com força total: as leituras lógicas saltam de **77.448** para **282.476 páginas** (**aumento de +264,73%!**) e o tempo mais que dobra, indo de **502,0 ms** para **1.098,5 ms (1,1 segundo!)** (**Speedup de 0,46x**, estatisticamente significativo com $p = 0,00195$).

---

## Parte 5 — Explicação Completa dos Resultados e Gráficos

### 5.1. Tabela Geral de Resultados — Warm Cache ($N = 30$)
Esta é a tabela principal que está no artigo ([paper/main.pdf](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/paper/main.pdf)) e nos slides:

| Consulta | O que testa | Leituras Base | Leituras Otim. | Redução de E/S | Tempo Base (ms) | Tempo Otim. (ms) | Speedup | Significância ($p$-valor) |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | :---: | :--- |
| **Q1** | Busca pontual por `Email` | 2.856 | 6 | **99,79%** | 15,0 ± 4,4 | **< 1** ± 0,0 | **> 15x** | $p < 10^{-4}$ (Wilcoxon) |
| **Q2** | Faixa de datas em `Pedidos` | 8.090 | 34 | **99,58%** | 104,5 ± 96,9 | **1,5** ± 1,8 | **69,7x** | $p < 10^{-4}$ (Wilcoxon) |
| **Q3** | Composto `(Status, Data)` | 8.090 | 17 | **99,79%** | 87,0 ± 17,5 | **1,0** ± 0,6 | **87,0x** | $p < 10^{-4}$ (Wilcoxon) |
| **Q4** | Cobertura `INCLUDE` (s/ Lookup) | 8.090 | 5 | **99,94%** | 111,0 ± 62,9 | **< 1** ± 0,3 | **> 111x** | $p < 10^{-4}$ (Wilcoxon) |
| **Q5** | Join de 3 tabelas (FKs) | 28.818 | 5.295 | **81,63%** | 450,0 ± 19,4 | **12,0** ± 2,4 | **37,5x** | $p < 10^{-4}$ (Wilcoxon) |
| **Q6** | `TOP 50` s/ operador `Sort` | 8.090 | 3 | **99,96%** | 424,0 ± 25,0 | **< 1** ± 0,0 | **> 424x** | $p < 10^{-4}$ (Wilcoxon) |
| **Q7** | ⚠️ Agregação (*Batch* vs *Row*) | 8.090 | 5.658 | **30,06%** | **217,0** ± 11,8 | 364,0 ± 36,0 | **0,60x (Piorou)** | $p < 10^{-4}$ (Wilcoxon) |
| **Q8** | `LIKE` com prefixo sargable | 637 | 28 | **95,60%** | 114,0 ± 3,6 | **1,0** ± 0,4 | **114,0x** | $p < 10^{-4}$ (t-Student) |
| **Q9** | Data sem função `YEAR()` | 8.090 | 1.565 | **80,66%** | 226,0 ± 17,9 | **26,0** ± 1,8 | **8,69x** | $p < 10^{-4}$ (Wilcoxon) |
| **Q10** | Subconsulta vs `NOT EXISTS` | 10.946 | 8.252 | **24,61%** | 370,5 ± 34,2 | **219,5** ± 23,9 | **1,69x** | $p < 10^{-4}$ (Wilcoxon) |
| **W1** | ⚠️ `INSERT` de 10.000 itens | 97.154 | 180.057 | **-85,33% (Subiu)** | **384,0** ± 113,9 | 404,0 ± 853,2 | **0,95x** | $p = 0,129$ (Wilcoxon) |

### 5.2. O que cada um dos 5 Gráficos (`paper/figures/`) mostra?
Quando você olhar para os slides ou para o PDF do artigo, verá 5 figuras geradas pelo nosso código:
1. **[fig1_leituras_logicas.png](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/paper/figures/fig1_leituras_logicas.png) (Slide 6 / Slide 8 do roteiro):**
   - Gráfico de barras comparando as **Leituras Lógicas** do Baseline (azul) vs. Otimizado (verde nas leituras, vermelho na escrita W1).
   - **Atenção:** O eixo Y está em **escala logarítmica** ($1, 10, 100, 1.000, 10.000, 100.000$), porque se fosse escala normal, uma barra de `3` páginas (Q6) perto de uma de `180.057` páginas (W1) nem apareceria na tela!
2. **[fig2_tempos_execucao_boxplot.png](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/paper/figures/fig2_tempos_execucao_boxplot.png) (Slide 7 do Beamer):**
   - Mostra os **Boxplots (diagramas de caixa)** das 30 execuções de cada consulta em milissegundos e o Speedup alcançado. Mostra visualmente como os tempos otimizados ficam colados no zero nas consultas seletivas.
3. **[fig3_q4_tres_estagios.png](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/paper/figures/fig3_q4_tres_estagios.png) (Slide 8 do Beamer / Slide 9 do roteiro):**
   - Mostra a escadinha da **Q4**: como saímos de `8.090` páginas no Scan, caímos para `1.296` páginas quando criamos um índice simples (mas sofremos 422 *Key Lookups*), e finalmente chegamos a `5` páginas quando adicionamos `INCLUDE (DataPedido, ValorTotal)`.
4. **[fig4_warm_vs_cold_cache.png](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/paper/figures/fig4_warm_vs_cold_cache.png) (Slide 10 do Beamer / Slide 11 do roteiro):**
   - Compara o tempo em **Warm Cache (memória quente)** contra **Cold Cache (memória fria, lendo do SSD)**. Mostra que mesmo limpando a RAM, as consultas indexadas continuam muito mais rápidas, enquanto a escrita **W1** explode para `1.098,5 ms`.
5. **[fig5_planos_execucao.png](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/paper/figures/fig5_planos_execucao.png) (Slide 9 do Beamer / Slide 10 do roteiro):**
   - Desenha lado a lado os fluxogramas dos operadores físicos extraídos dos arquivos `.sqlplan` reais para **Q1**, **Q4**, **Q7** e **W1**.

---

## Parte 6 — Como Funciona o Código do Projeto? (Arquivo por Arquivo)

Nosso repositório foi totalmente automatizado em **Python + SQL + Docker**. Você não precisa decorar cada linha de Python, mas entender o que cada arquivo faz dá total segurança na apresentação:

### 6.1. Infraestrutura na Raiz
* **[docker-compose.yml](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/docker-compose.yml):** Sobe o container `bd2_sqlserver` com a imagem oficial `mcr.microsoft.com/mssql/server:2022-latest` (SQL Server 2022 Developer Edition no Ubuntu). Ele trava o limite de memória RAM do container em **4 GB (`mem_limit: 4g`)**, mapeia a porta `1433` e monta a pasta `./data` dentro do container em `/var/opt/mssql/csv_data`.
* **[pyproject.toml](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/pyproject.toml):** Define as bibliotecas Python usadas pelo projeto: `pymssql` (para conectar no SQL Server), `numpy` (para gerar os 6,25 milhões de dados rápido), `scipy` (para fazer os testes estatísticos de Shapiro-Wilk, t-Student e Wilcoxon) e `matplotlib` (para desenhar os 5 gráficos).

### 6.2. Os 4 Scripts SQL de Construção do Banco (`scripts/sql/`)
1. **[01_create_baseline_db.sql](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/sql/01_create_baseline_db.sql):** Cria o banco `Ecommerce_Baseline`, configura `RECOVERY SIMPLE` (para não inchar o log de transações durante a carga) e cria as 4 tabelas (`Clientes`, `Produtos`, `Pedidos`, `ItensPedido`) apenas com suas `PRIMARY KEY CLUSTERED` e `FOREIGN KEY`.
2. **[02_bulk_load_baseline.sql](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/sql/02_bulk_load_baseline.sql):** Desativa temporariamente as FKs para carregar rápido, executa `BULK INSERT` dos 4 arquivos CSV em lotes de `100.000` linhas (`BATCHSIZE = 100000`), reativa as FKs com `WITH CHECK CHECK CONSTRAINT ALL` (garantindo que o SQL Server confie nas FKs, deixando `is_not_trusted = 0`) e roda `DBCC CHECKCONSTRAINTS`.
3. **[03_backup_and_clone.sql](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/sql/03_backup_and_clone.sql):** Faz o `BACKUP DATABASE [Ecommerce_Baseline]` gerando o arquivo `ecommerce_init.bak` e em seguida roda `RESTORE DATABASE [Ecommerce_Otimizado] ... WITH MOVE`, criando a base gêmea idêntica.
4. **[04_create_indexes_optimized.sql](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/sql/04_create_indexes_optimized.sql):** Entra na base `Ecommerce_Otimizado`, cria os **9 índices secundários** e executa `EXEC sp_updatestats` para atualizar as estatísticas do otimizador.

### 6.3. Os Scripts Python de Automação (`scripts/`)
* **[db.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/db.py):** Centraliza a conexão com o SQL Server (`127.0.0.1:1433`, usuário `sa`, senha `Bd2Trabalho!2026`).
* **[generate_data.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/generate_data.py):** Gera os 4 arquivos CSV na pasta `data/` usando `seed=42`. Calcula até o `ValorTotal` de cada pedido somando `Quantidade * PrecoUnitario * (1 - Desconto)` dos seus itens para que o banco seja 100% realista!
* **[create_schema.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/create_schema.py), [load_baseline.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/load_baseline.py) e [clone_optimized.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/clone_optimized.py):** Executam os scripts SQL `01`, `02` e `03` e conferem se as contagens de linhas e os acentos em português (`Goiânia`, `Móveis`) foram gravados sem erro.
* **[queries.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/queries.py):** Guarda o catálogo oficial das 11 consultas (`Q1` a `Q10` e `W1`), com o SQL do Baseline e o SQL do Otimizado.
* **[metrics.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/metrics.py):** É o "extrator de métricas". Ele intercepta as mensagens que o SQL Server devolve quando ligamos `SET STATISTICS IO, TIME ON` e usa expressões regulares (Regex) para extrair `logical_reads`, `physical_reads`, `cpu_time_ms` e `elapsed_time_ms`. Também captura o plano de execução real em XML (`SET STATISTICS XML ON`) e garante que `W1` sempre rode dentro de `BEGIN TRANSACTION ... ROLLBACK TRANSACTION`.
* **[apply_optimizations.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/apply_optimizations.py):** Primeiro cria o índice simples temporário em `Pedidos(ClienteID)` para medir e salvar o plano do **Estágio 2 da Q4** (`q4_intermediate_lookup.sqlplan`), e depois aplica os 9 índices finais em `Ecommerce_Otimizado` e salva todos os planos `.sqlplan` em `results/plans/optimized/`.
* **[run_benchmarks.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/run_benchmarks.py):** Roda as **880 execuções oficiais**:
  - Para cada uma das 11 consultas: faz 2 aquecimentos descartados + **30 rodadas pareadas em Warm Cache** (alternando quem roda primeiro nas rodadas ímpares e pares para não favorecer nenhuma base!) + **10 rodadas pareadas em Cold Cache** (limpando a memória antes de cada execução).
  - Salva tudo em `results/benchmark_runs.csv` e `results/benchmark_runs.json`.
* **[analyze_results.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/analyze_results.py):** Lê as 880 medições, calcula média, mediana, desvio padrão, intervalo de confiança de 95%, Speedup e aplica Shapiro-Wilk + Teste t ou Wilcoxon, gerando automaticamente a tabela do artigo em LaTeX (`paper/generated/tabela_resultados.tex`) e o resumo em `results/summary_table.csv`.
* **[generate_charts.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/generate_charts.py) e [generate_plan_diagrams.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/generate_plan_diagrams.py):** Geram as 5 imagens PNG de alta resolução (300 DPI) na pasta `paper/figures/`.
* **[test_demo_kit.py](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/test_demo_kit.py):** Testa automaticamente os 4 scripts da demonstração ao vivo (`scripts/demo/01` a `04`) para garantir que nada vai dar erro na frente do professor!

---

## Parte 7 — Explicação dos Slides e dos Roteiros (Integrante por Integrante)

A nossa apresentação tem tempo limite de **20 minutos** (planejada para **~17 minutos**, deixando 3 minutos de folga).
A equipe de **5 integrantes** foi dividida assim nos roteiros da pasta `slides/`:

| Quem | Papel na Apresentação | Tempo Alvo | Arquivo de Roteiro Individual |
| :--- | :--- | :---: | :--- |
| **Integrante 1** | **Slides 1 a 3:** Abertura, Problema de Pesquisa e Teoria de Árvore B+ / Modos de Execução | ~2m00s (máx 2m30s) | [roteiro-slides-integrante-1.pdf](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/slides/roteiro-slides-integrante-1.pdf) |
| **Integrante 2** | **Slides 4 a 7:** Como o projeto funciona, Bases Gêmeas (6,25M linhas e 9 índices), Consultas Q1–Q10/W1 e Reescritas Sargable | ~4m00s (máx 4m45s) | [roteiro-slides-integrante-2.pdf](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/slides/roteiro-slides-integrante-2.pdf) |
| **Integrante 3** | **Slides 8 a 12:** Resultados de E/S, Estudo de Caso Q4 em 3 Estágios, Planos XML, Trade-offs (Q7 e W1) e Conclusão | ~2m00s (máx 2m45s) | [roteiro-slides-integrante-3.pdf](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/slides/roteiro-slides-integrante-3.pdf) |
| **Integrante 4** | **Prática ao Vivo — Parte A:** Mostrar `docker-compose.yml`, os 9 índices e rodar ao vivo **Demo 01 (Q1)** e **Demo 02 (Q3)** no VS Code | ~4m30s (máx 5m00s) | [roteiro-apresentacao-pratica.pdf](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/slides/roteiro-apresentacao-pratica.pdf) |
| **Integrante 5** | **Prática ao Vivo — Parte B:** Rodar ao vivo **Demo 03 (Q4)** + abrir plano intermediário, rodar **Demo 04 (W1)** com `ROLLBACK` e mostrar os planos da **Q7** | ~4m30s (máx 5m00s) | [roteiro-apresentacao-pratica.pdf](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/slides/roteiro-apresentacao-pratica.pdf) |

> **Nota sobre a numeração dos slides:** Nos roteiros individuais (`roteiro-slides-integrante-1/2/3.pdf`, feitos para os 12 slides do Canva) a sequência vai do **Slide 1 ao Slide 12**. No arquivo PDF compilado em Beamer ([slides/apresentacao.pdf](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/slides/apresentacao.pdf)), existem **13 páginas** (a Capa + 12 seções numeradas de `1.` a `12.`). Abaixo explicamos cada slide indicando exatamente a correspondência!

---

### 👤 Etapa 1: Integrante 1 (Slides 1 a 3 — Abertura e Fundamentos)

#### **Slide 1 — Capa e Abertura (~20 segundos)**
* **O que está na tela:** Título do trabalho, nomes da equipe e contexto (6,25 milhões de linhas no SQL Server 2022).
* **O que você está dizendo e o que significa:** Você cumprimenta o professor e a turma, diz que o grupo investigou na prática como índices, reescrita de consultas SQL e operadores físicos mudam o desempenho do SQL Server 2022 em um banco de e-commerce com **6,25 milhões de registros**, e avisa que os slides serão rápidos (~8 minutos) para deixar metade da apresentação para a demonstração ao vivo no computador.

#### **Slide 2 — Contexto e Problema de Pesquisa (~50 segundos)**
* **O que está na tela:** Os problemas de bancos grandes (*Scan* $O(N)$, *Key Lookup*, SQL não-*sargable*) e o alerta sobre o "Mito do Índice Gratuito".
* **Como entender para explicar sem decorar:**
  1. Quando uma tabela tem milhões de linhas, ler a tabela toda (*Scan*, custo $O(N)$) entope a memória RAM (*buffer pool*), mesmo que o computador tenha SSD rápido.
  2. Mas sair criando índices de qualquer jeito dá errado por **3 motivos**:
     - Se o índice não tiver todas as colunas que o `SELECT` pede, o banco sofre com centenas de **Key Lookups** (pulos de volta na tabela principal).
     - Se o programador colocar funções no `WHERE` (como `YEAR(Data)`) ou `%` no começo do `LIKE`, o índice fica **bloqueado** (consulta não-*sargable*).
     - Existe o **mito do índice gratuito**: todo índice criado deixa o `SELECT` rápido, mas deixa o `INSERT/UPDATE/DELETE` mais lento porque precisa atualizar várias árvores ao mesmo tempo.

#### **Slide 3 — Fundamentos: Árvore B+ e Planos de Execução (~50 segundos)**
* **O que está na tela:** Árvore B+ em páginas de 8 KB, índice clusterizado vs. não-clusterizado (`INCLUDE`, composto, filtrado), sargabilidade e operadores de Join + *Batch Mode*.
* **Como entender para explicar sem decorar:**
  - Os índices do SQL Server são **Árvores B+** guardadas em páginas de 8 KB. Como os nós do meio só guardam chaves curtas, a árvore é baixinha (2 a 4 andares) e acha qualquer dado em pouquíssimas leituras ($O(\log_m N)$).
  - **Clusterizado** é a própria tabela ordenada pela chave primária (só 1 por tabela); **Não-clusterizado** é uma árvore separada que pode usar `INCLUDE` para guardar colunas extras nas folhas (índice de cobertura).
  - Nos operadores físicos, o SQL Server 2022 tem três tipos de Join (*Nested Loops*, *Merge Join*, *Hash Match*) e tem o modo vetorizado **Batch Mode on Rowstore**, que processa lotes de até ~900 linhas de uma vez — e é justamente isso que explica o caso curioso da nossa consulta **Q7**!

---

### 👤 Etapa 2: Integrante 2 (Slides 4 a 7 — Metodologia, Esquema e Consultas)

#### **Slide 4 — Como o Projeto Funciona / Fluxo Experimental (~55 segundos)**
* **O que está na tela:** O fluxograma de 4 passos: `1. Base Seed 42 (6,25M linhas)` $\rightarrow$ `2. Clone Gêmeo (BACKUP/RESTORE)` $\rightarrow$ `3. 9 Índices B+ (Base Otimizada)` $\rightarrow$ `4. Benchmark (880 execuções)`.
* **Como entender para explicar sem decorar:**
  - Explicar como montamos um laboratório justo: subimos o SQL Server 2022 em container Docker limitado a **4 GB de RAM**.
  - Geramos os 6,25 milhões de registros com `seed = 42` no banco `Ecommerce_Baseline`.
  - Fizemos um `BACKUP` e `RESTORE` para criar o banco irmão gêmeo `Ecommerce_Otimizado` (assim os dois têm exatamente os mesmos dados iniciais).
  - Criamos os **9 índices secundários** apenas no `Ecommerce_Otimizado`.
  - Rodamos um script Python que executou **880 medições** com `OPTION (MAXDOP 1)` (1 thread) para comparar os dois bancos sem interferência externa, usando `ROLLBACK` na carga de escrita `W1`.

#### **Slide 5 — As Bases Gêmeas e o Esquema B2C (~1 minuto)**
* **O que está na tela:** As 4 tabelas (`Clientes` 200k, `Produtos` 50k, `Pedidos` 1,5M, `ItensPedido` 4,5M) e o comparativo: `Baseline` (0 índices secundários) vs. `Otimizado` (9 índices secundários).
* **Como entender para explicar sem decorar:**
  - Basta apontar os números das 4 tabelas que somam **6,25 milhões de linhas (~400 MB)** e resumir onde entraram os 9 índices na base Otimizada: 1 em `Clientes` (e-mail), 1 em `Produtos` (nome com `INCLUDE`), 4 em `Pedidos` (cobrindo data, status+data, cliente e status) e 3 em `ItensPedido` (incluindo o índice filtrado para descontos `>= 10.00`).

#### **Slide 6 — A Suíte Experimental: Q1 a Q10 e W1 (~1m05s)**
* **O que está na tela:** A tabela resumindo o que cada consulta de **Q1 a Q10** e **W1** faz.
* **Como entender para explicar sem decorar:**
  - Apresente as consultas por grupos (como você viu na Parte 4 deste guia):
    - **Q1 e Q2:** buscas simples (1 e-mail específico e 1 semana de pedidos).
    - **Q3:** índice composto (`Status = 'ENTREGUE'` + intervalo de `DataPedido`).
    - **Q4:** nosso estudo em 3 estágios para eliminar 422 *Key Lookups* usando `INCLUDE`.
    - **Q5 e Q10:** junção de 3 tabelas (`JOIN`) e busca de clientes sem pedidos (`NOT EXISTS`).
    - **Q6:** paginação dos 50 pedidos mais recentes (`TOP 50 ORDER BY DataPedido DESC`) eliminando o operador `Sort`.
    - **Q8 e Q9:** conserto de consultas não-*sargable* em texto (`LIKE`) e data (`YEAR()`).
    - **Q7 e W1:** nossos dois testes de limites/trade-offs (soma geral por status e inserção de 10.000 itens).

#### **Slide 7 — Reescritas Sargable (Q8, Q9, Q10) e Protocolo Estatístico (~1 minuto)**
* **O que está na tela:** Os blocos de código SQL do "Antes vs. Depois" de Q8, Q9 e Q10, mais o protocolo Warm ($N=30$) e Cold ($N=10$).
* **Como entender para explicar sem decorar:**
  - **Em Q8:** Trocamos `LIKE N'%Notebook%'` por `LIKE N'Notebook%'` (lembrando do prefixo `N` por ser `NVARCHAR` e explicando que isso vale porque o catálogo começa pelo nome da categoria).
  - **Em Q9:** Trocamos `YEAR(DataPedido) = 2025` por `DataPedido >= '2025-01-01' AND DataPedido < '2026-01-01'` para o banco não ter que calcular função em 1,5 milhão de linhas.
  - **Em Q10:** Trocamos a subconsulta `MAX(DataPedido) IS NULL` por `NOT EXISTS`, permitindo um *Left Anti Semi Join*.
  - Finalize dizendo que rodamos 30 vezes em Warm Cache e 10 vezes em Cold Cache (limpando a memória com `DROPCLEANBUFFERS` e `FREEPROCCACHE`) e validamos com Shapiro-Wilk + Teste t ou Wilcoxon.

---

### 👤 Etapa 3: Integrante 3 (Slides 8 a 12 — Resultados, Gráficos, Trade-offs e Conclusão)

#### **Slide 8 (Seção 6 e 7 no Beamer) — Resultados de E/S Lógica e Speedup em Warm Cache (~30 segundos)**
* **O que está na tela:** O gráfico de barras em escala logarítmica ([fig1_leituras_logicas.png](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/paper/figures/fig1_leituras_logicas.png)) (e no Beamer também o boxplot de tempos [fig2_tempos_execucao_boxplot.png](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/paper/figures/fig2_tempos_execucao_boxplot.png)).
* **Como entender para explicar sem decorar:**
  - Aponte para o gráfico: das 10 consultas de leitura, **9 tiveram quedas gigantescas de leitura e tempo** (todas com $p < 10^{-4}$).
  - Cite os 3 campeões: **Q6** caiu de `8.090` para `3` páginas (**-99,96%** e mais de **424x mais rápida**); **Q8** ficou **114x mais rápida**; e **Q5** (o join de 3 tabelas) caiu de `450 ms` para `12 ms` (**37,5x mais rápida**).
  - Aponte para a barra vermelha na direita (**W1**): na escrita de 10.000 linhas, as leituras de páginas subiram **+85,33%** por ter que atualizar os índices!

#### **Slide 9 (Seção 8 no Beamer) — Estudo de Caso Q4 em 3 Estágios (~25 segundos)**
* **O que está na tela:** O gráfico de 3 barras da Q4 ([fig3_q4_tres_estagios.png](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/paper/figures/fig3_q4_tres_estagios.png)).
* **Como entender para explicar sem decorar:**
  - Conte a história das 3 barras:
    1. Sem índice (Baseline), ler os 422 pedidos custava **8.090 páginas (111 ms)** porque varria a tabela toda.
    2. Com um índice simples só em `ClienteID`, o tempo caiu para **1 ms**, mas o banco ainda leu **1.296 páginas** porque precisou dar **422 pulos (*Key Lookups*)** na tabela principal para buscar `DataPedido` e `ValorTotal`.
    3. Quando colocamos `INCLUDE (DataPedido, ValorTotal)` no índice, os pulos sumiram e a leitura despencou para apenas **5 páginas (< 1 ms, -99,94%)**!

#### **Slide 10 (Seção 9 no Beamer) — Evidência Direta nos Planos Físicos Reais (~20 segundos)**
* **O que está na tela:** A figura com os 4 diagramas dos planos `.sqlplan` ([fig5_planos_execucao.png](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/paper/figures/fig5_planos_execucao.png)).
* **Como entender para explicar sem decorar:**
  - Diga que esses diagramas vieram direto do XML do SQL Server: em **(a) Q1** e **(b) Q4** vemos a troca de *Scan* por *Seek* e o sumiço do *Key Lookup*; já em **(c) Q7** vemos a troca de *Hash Match* por *Stream Aggregate*, e em **(d) W1** vemos o operador *Sequence* dividindo o `INSERT` em 4 árvores B+ ao mesmo tempo.

#### **Slide 11 (Seção 10 no Beamer) — Os Trade-offs Reais: Q7, W1 e Cold Cache (~25 segundos)**
* **O que está na tela:** A explicação da **Q7** (*Batch Mode* vs. *Row Mode*) e o gráfico **Warm vs. Cold Cache** ([fig4_warm_vs_cold_cache.png](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/paper/figures/fig4_warm_vs_cold_cache.png)).
* **Como entender para explicar sem decorar:**
  - **Sobre a Q7:** Explique com orgulho! *"Em Q7, o índice reduziu as páginas lidas em 30% (de 8.090 para 5.658), mas o tempo subiu de 217 ms para 364 ms (0,60x). Por quê? Porque no Baseline o Hash Match rodou em Batch Mode (processando pacotes vetorizados de 900 linhas), enquanto com o índice o banco escolheu um Stream Aggregate em Row Mode (linha por linha)."*
  - **Sobre o Cold Cache e W1:** Mesmo limpando a memória RAM, as leituras otimizadas continuam muito superiores (ex.: Q5 é 4,33x mais rápida), mas a escrita **W1** no cache frio sofre pesado: sobe **+264,7% em E/S** e passa de 1 segundo (**1.098,5 ms**).

#### **Slide 12 (Seções 11 e 12 no Beamer) — Conclusão e Passagem para a Prática ao Vivo (~20 segundos)**
* **O que está na tela:** Síntese dos ganhos (até 99,96%), lição de engenharia (sempre olhar `STATISTICS IO/TIME` e o plano real) e chamada para a demonstração ao vivo.
* **Como entender para explicar sem decorar:**
  - Feche dizendo que índices bem desenhados trazem ganhos enormes, mas que Q7 e W1 provam que nunca se deve criar índices no escuro sem medir E/S, tempo e plano de execução. Em seguida, passe a palavra para os **Integrantes 4 e 5** mostrarem tudo rodando ao vivo no VS Code!

---

### 💻 Etapa 4: Integrantes 4 e 5 (Roteiro da Apresentação Prática ao Vivo — 9 a 10 minutos)

O roteiro completo está em [slides/roteiro-apresentacao-pratica.pdf](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/slides/roteiro-apresentacao-pratica.pdf). Veja como é simples: **vocês não vão digitar uma única linha de código na hora!** Tudo já está pronto nas abas do VS Code.

#### **Preparação 15 minutos antes de começar a apresentação:**
1. Subir o container Docker: `docker compose up -d --wait`
2. Deixar abertas no VS Code, da esquerda para a direita, estas abas:
   - Aba 1: [docker-compose.yml](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/docker-compose.yml)
   - Aba 2: [scripts/sql/04_create_indexes_optimized.sql](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/sql/04_create_indexes_optimized.sql)
   - Aba 3: [scripts/demo/01_q1_seek_vs_scan.sql](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/demo/01_q1_seek_vs_scan.sql)
   - Aba 4: [scripts/demo/02_q3_indice_composto.sql](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/demo/02_q3_indice_composto.sql)
   - Aba 5: [scripts/demo/03_q4_eliminacao_key_lookup.sql](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/demo/03_q4_eliminacao_key_lookup.sql)
   - Aba 6: [results/plans/optimized/q4_intermediate_lookup.sqlplan](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/results/plans/optimized/q4_intermediate_lookup.sqlplan)
   - Aba 7: [scripts/demo/04_w1_tradeoff_escrita.sql](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/scripts/demo/04_w1_tradeoff_escrita.sql)
   - Aba 8 e 9: [q7_baseline.sqlplan](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/results/plans/baseline/q7_baseline.sqlplan) e [q7_optimized.sqlplan](file:///c:/Users/MWSS/OneDrive/Desktop/Trabalho-Final-BD2/results/plans/optimized/q7_optimized.sqlplan)
3. Conectar as 4 abas `.sql` (`01` a `04`) no banco e **ativar o botão "Enable Actual Plan" (`Ctrl+M`)** em cada uma delas.

#### **O que o Integrante 4 faz (~4m30s):**
1. **Mostra a infraestrutura (1 min):** Aponta o limite `mem_limit: 4g` no `docker-compose.yml` e passa rapidamente pelos 9 índices criados em `04_create_indexes_optimized.sql`.
2. **Roda a Demo 01 — Q1 (`Ctrl+Shift+E` na aba `01_q1_seek_vs_scan.sql`):**
   - Cada script de demo já roda primeiro no `USE Ecommerce_Baseline;` e logo abaixo no `USE Ecommerce_Otimizado;`!
   - Na aba **Messages**, aponta: o Baseline fez `logical reads 2856`, enquanto o Otimizado fez `logical reads 6` (**-99,79%**).
   - Na aba **Query Plan**, mostra o desenho: em cima um `Clustered Index Scan` varrendo a tabela toda; embaixo um `Index Seek` + `1 Key Lookup`.
3. **Roda a Demo 02 — Q3 (`Ctrl+Shift+E` na aba `02_q3_indice_composto.sql`):**
   - Na aba **Results**, mostra que ambos retornaram `3.198 linhas`.
   - Na aba **Messages**, aponta: o Baseline leu `8090` páginas; o Otimizado leu apenas `17` páginas (**87x mais rápido**).
   - Na aba **Query Plan**, mostra que o Otimizado tem um único `Index Seek` no índice composto `(Status, DataPedido)`, sem nenhum Lookup! Passa a vez para o Integrante 5.

#### **O que o Integrante 5 faz (~4m30s):**
1. **Roda a Demo 03 — Q4 (`Ctrl+Shift+E` na aba `03_q4_eliminacao_key_lookup.sql`) + Plano Intermediário:**
   - Na aba **Messages**, mostra que para retornar `422 linhas`, o Baseline leu `8090` páginas e o Otimizado com `INCLUDE` leu apenas `5` páginas (**-99,94%**).
   - Clica na aba vizinha `q4_intermediate_lookup.sqlplan` e mostra para a banca como era quando não tinha o `INCLUDE`: aponta a caixinha do `Key Lookup (Clustered)` consumindo **99,6% do custo da consulta** (1.296 páginas por causa das 422 idas à tabela base).
2. **Roda a Demo 04 — W1 (`Ctrl+Shift+E` na aba `04_w1_tradeoff_escrita.sql`):**
   - Explica que o script insere `10.000 linhas` dentro de `BEGIN TRAN ... ROLLBACK` e mostra no **Results** que a tabela continua com `4.500.000` linhas intactas.
   - Na aba **Messages**, mostra o salto de páginas lidas/escritas (de ~97 mil para ~180 mil páginas).
   - Na aba **Query Plan**, mostra a diferença visual impressionante: no Baseline há apenas 1 caixinha `Clustered Index Insert`; no Otimizado há o operador `Sequence` empurrando dados para **4 caixinhas de Insert** (a PK + os 3 índices secundários).
3. **Mostra o Insight da Q7 e encerra:**
   - Clica nas abas `q7_baseline.sqlplan` e `q7_optimized.sqlplan` (ou resume verbalmente se o tempo estiver no fim): mostra que o Baseline usou `Hash Match` em **Batch Mode** (217 ms) e o Otimizado usou `Stream Aggregate` em **Row Mode** (364 ms), encerrando a apresentação e abrindo para perguntas!

---

## Parte 8 — Perguntas que o Professor Pode Fazer (E Como Responder)

Se o professor perguntar qualquer uma destas coisas na hora da arguição, você já tem a resposta na ponta da língua:

1. **"Por que vocês escolheram o SQL Server 2022 em Docker?"**
   - **Resposta:** *"Primeiro, porque o edital pedia um SGBD comercial robusto e vedava o uso do MySQL. Segundo, porque o SQL Server 2022 oferece métricas nativas exatas de páginas com `SET STATISTICS IO, TIME ON` e planos de execução completos em XML (`ShowPlanXML`), além de recursos modernos como índices com `INCLUDE`, índices filtrados e `Batch Mode on Rowstore`. E colocamos em Docker com limite de 4 GB de RAM para garantir que o experimento rode de forma idêntica tanto no Windows quanto no Linux."*

2. **"Por que todas as consultas têm `OPTION (MAXDOP 1)` no final?"**
   - **Resposta:** *"O `MAXDOP 1` força cada consulta a rodar em uma única thread de CPU. Se deixássemos o paralelismo solto dentro de um container Docker, o escalonador do sistema operacional poderia dar mais threads em uma rodada e menos em outra, gerando ruído nos tempos. Com `MAXDOP 1`, isolamos 100% o efeito matemático da estrutura do índice e do operador físico."*

3. **"Na consulta Q7, o índice deixou a consulta mais lenta (de 217 ms para 364 ms). Isso significa que o índice deu errado?"**
   - **Resposta:** *"Em termos de leitura de páginas (E/S), o índice funcionou: ele reduziu as leituras em 30,06% (de 8.090 para 5.658 páginas) e eliminou o gasto de memória RAM do Hash Match. O tempo de CPU subiu porque, no Baseline, o SQL Server 2022 executou o Hash Match usando `Batch Mode on Rowstore` (processando pacotes vetorizados de até 900 linhas por vez), enquanto o índice levou o otimizador a escolher um `Stream Aggregate`, que só roda em `Row Mode` (linha a linha). Mantivemos esse resultado no artigo justamente para provar que menos leitura de página nem sempre significa menor tempo de CPU."*

4. **"Na consulta Q8, trocar `LIKE '%Notebook%'` por `LIKE 'Notebook%'` muda o significado da consulta?"**
   - **Resposta:** *"Sim, em um texto livre mudaria, pois `'Notebook%'` busca apenas no início do texto (prefixo) e `'%Notebook%'` busca em qualquer posição. No nosso banco de e-commerce, todos os nomes de produtos são padronizados começando pelo tipo do produto (ex.: `'Notebook Pro Serie 10'`), por isso as duas consultas retornam exatamente as mesmas 2.002 linhas. Nós deixamos explícito no artigo que, se o sistema precisasse buscar palavras soltas no meio de descrições livres, um índice B+ não resolveria e seria necessário usar um índice invertido de Full-Text Search."*

5. **"Como vocês rodaram 40 vezes o teste de escrita `W1` (inserindo 10.000 linhas cada vez) sem sujar o banco de dados?"**
   - **Resposta:** *"Cada execução de `W1` roda dentro de um bloco `BEGIN TRANSACTION ... ROLLBACK TRANSACTION`. O coletor Python captura as métricas do `SET STATISTICS IO, TIME ON` imediatamente após o `INSERT` — quando o SQL Server já fez todas as leituras, ordenações e inserções nas 4 árvores B+ — e em seguida executa o `ROLLBACK`, mantendo a tabela `ItensPedido` cravada em 4.500.000 linhas do início ao fim."*
