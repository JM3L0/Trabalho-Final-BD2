# Roteiro de Apresentação — 15 Minutos (5 Integrantes, 10 Slides)

**Título:** Análise Experimental de Indexação, Planos de Execução e Otimização de Consultas no Microsoft SQL Server 2022  
**Arquivos da Apresentação:** `slides/apresentacao_15min.pdf` e `slides/apresentacao_15min.pptx` (10 slides — 16:9)  
**Duração total:** **15 minutos** (**3 minutos por integrante** | **2 slides por integrante**)

> **Dica de ritmo:** Com apenas **2 slides por pessoa** em **3 minutos**, cada integrante tem tempo confortável para falar com calma (~1m30s por slide), apontando diretamente para os prints das tabelas e figuras do artigo sem pressa.

---

## Quadro Resumo de Tempo e Divisão

| Integrante | Responsável (ordem do artigo) | Slides | Bloco Temático | Duração | Acumulado |
| :--- | :--- | :---: | :--- | :---: | :---: |
| **Integrante 1** | Hermeson A. | 1 e 2 | Capa, Introdução e Fundamentação | 3m00s | 03:00 |
| **Integrante 2** | João Marcos R. | 3 e 4 | Metodologia, Bases Gêmeas, Índices e Protocolo | 3m00s | 06:00 |
| **Integrante 3** | Lizzandro W. | 5 e 6 | Resultados em *Warm Cache* (Tab. 3, Fig. 1 e Fig. 2) | 3m00s | 09:00 |
| **Integrante 4** | Marcos W. | 7 e 8 | Caso $Q_4$ (*Key Lookup*) e Planos Físicos (`.sqlplan`) | 3m00s | 12:00 |
| **Integrante 5** | Raildom R. | 9 e 10 | *Trade-offs*, *Cold Cache*, Conclusão e Referências | 3m00s | 15:00 |

---

## Integrante 1 — Hermeson A. (Slides 1 e 2 | 00:00 – 03:00)

### Slide 1 — Capa (00:00 – 00:35 | 35s)
- **Ação:** Abertura e apresentação do tema e da equipe.
- **Fala sugerida:**
  > "Boa tarde a todos. Somos alunos do Bacharelado em Sistemas de Informação da UFPI, campus CSHNB em Picos, e vamos apresentar o trabalho *Análise Experimental de Indexação, Planos de Execução e Otimização de Consultas no Microsoft SQL Server 2022*. A apresentação será conduzida pelos cinco integrantes do grupo: eu, Hermeson, seguido por João Marcos, Lizzandro, Marcos e Raildom."

### Slide 2 — Introdução e Fundamentação (00:35 – 03:00 | 2m25s)
- **Ação:** Percorrer os 4 tópicos conectando o problema prático aos conceitos de árvore B+ e otimização que sustentam o experimento.
- **Fala sugerida:**
  > "Em bancos relacionais que processam milhões de registros, o maior fator de latência é o custo de entrada e saída e a varredura sequencial de páginas. Mesmo com muita memória RAM e SSDs rápidos, operações de *Table Scan* ou *Clustered Index Scan* elevam o tempo de resposta, disputam espaço no *buffer pool* e reduzem a capacidade concorrente.
  >
  > Para enfrentar isso, o projeto físico apoia-se em árvores B+ com páginas de 8 KB. Como os nós internos guardam apenas chaves de roteamento, a árvore mantém altura logarítmica $O(\log_m N)$, permitindo buscas pontuais em 2 a 4 acessos. Cada tabela tem um único índice clusterizado — com os dados ordenados nas folhas — enquanto índices não clusterizados apontam para a chave primária. Quando faltam colunas no índice secundário, ocorrem *Key Lookups* repetidos; para eliminá-los, usamos índices de cobertura com `INCLUDE`. Em contrapartida, índices exigem manutenção síncrona a cada modificação, causando amplificação de escrita.
  >
  > No plano lógico e físico, o otimizador por custos depende de predicados sargáveis — isolando a coluna indexada em buscas por prefixo, intervalos semiabertos ou reescrevendo subconsultas com `NOT EXISTS` — e escolhe entre *Nested Loops*, *Merge Join* e *Hash Match*, além do *Batch Mode on Rowstore*, que processa blocos em lote. Nosso objetivo foi medir esses ganhos e *trade-offs* no SQL Server 2022 em uma base com 6,25 milhões de linhas, avaliando dez leituras ($Q_1$–$Q_{10}$) e uma escrita em lote ($W_1$) sob cache quente e frio. Passo a palavra ao João Marcos."

---

## Integrante 2 — João Marcos R. (Slides 3 e 4 | 03:00 – 06:00)

### Slide 3 — Metodologia: Ambiente e Bases Gêmeas (03:00 – 04:30 | 1m30s)
- **Ação:** Apontar para o print da **Tabela 1** e explicar a construção das bases gêmeas.
- **Fala sugerida:**
  > "Obrigado, Hermeson. A Tabela 1 mostra o ambiente controlado do experimento: executamos o Microsoft SQL Server 2022 Developer 64-bit em um container Docker Ubuntu 22.04 limitado a 4 GB de RAM, sobre host Windows 11 com Core i5 de 12ª geração, 16 GB de RAM e SSD, tudo orquestrado via Python 3 com `uv` e `pymssql`.
  >
  > Projetamos um esquema normalizado de comércio eletrônico B2C povoado deterministicamente com `seed 42`: `Clientes` (200 mil linhas), `Produtos` (50 mil), `Pedidos` (1,5 milhão) e `ItensPedido` (4,5 milhões), somando 6,25 milhões de registros e 400 MB alocados, com cerca de 20% dos itens tendo desconto maior ou igual a 10,00.
  >
  > Para garantir comparação justa, atualizamos estatísticas em `Ecommerce_Baseline` — que contém apenas as 4 chaves primárias clusterizadas — e clonamos por `BACKUP` e `RESTORE` para gerar `Ecommerce_Otimizado`. Verificamos integridade referencial confiável (`is_not_trusted = 0`) e paridade absoluta nas 12 estatísticas iniciais antes de criar os índices."

### Slide 4 — Índices Secundários e Protocolo (04:30 – 06:00 | 1m30s)
- **Ação:** Apontar para o print da **Tabela 2** destacando exemplos de índices e explicar o protocolo de medição.
- **Fala sugerida:**
  > "A Tabela 2 lista os nove índices secundários criados em `Ecommerce_Otimizado` com amostragem estatística de 100%. Avaliamos quatro estratégias: índice simples (`IX_Clientes_Email`), índices de cobertura com `INCLUDE` em `Produtos`, `Pedidos` e `ItensPedido`, índice composto `(Status, DataPedido)` para igualdade e faixa em $Q_3$, e o índice filtrado `IX_ItensPedido_Desconto_Alto` (`WHERE Desconto >= 10.00`), cobrindo 901.180 linhas.
  >
  > A carga experimental envolve 10 consultas de leitura ($Q_1$–$Q_{10}$) e a inserção em lote de 10.000 itens ($W_1$), executada dentro de `BEGIN TRANSACTION ... ROLLBACK` para preservar exatamente 4,5 milhões de registros nas 880 medições.
  >
  > Todas as consultas rodaram com `OPTION (MAXDOP 1)` e literais tipados em dois regimes: *Warm Cache* ($N=30$ repetições pareadas após 2 aquecimentos) e *Cold Cache* ($N=10$ após esvaziar *buffer pool* e cache de planos). Aplicamos Shapiro-Wilk ($\alpha = 0{,}05$) para selecionar entre teste *t* pareado e Wilcoxon. Passo a palavra ao Lizzandro."

---

## Integrante 3 — Lizzandro W. (Slides 5 e 6 | 06:00 – 09:00)

### Slide 5 — Resultados em *Warm Cache* ($N = 30$) (06:00 – 07:30 | 1m30s)
- **Ação:** Apontar para o print da **Tabela 3**, destacando a coluna `Red. E/S`, `Speedup` e os contra-exemplos ($Q_7$ e $W_1$).
- **Fala sugerida:**
  > "Obrigado, João Marcos. A Tabela 3 apresenta os resultados medianos em *Warm Cache* ($N=30$). Em nove das dez consultas de leitura ($Q_1$–$Q_6$ e $Q_8$–$Q_{10}$), houve redução estatisticamente significativa ($p < 10^{-4}$) de páginas lidas e tempo de execução. Como o temporizador do SQL Server tem precisão de 1 ms, tempos abaixo de 0,5 ms em $Q_1$, $Q_4$ e $Q_6$ foram adotados conservadoramente como inferiores a 1 ms para o cálculo do *speedup*.
  >
  > O maior ganho ocorreu em $Q_6$ (`TOP 50` pedidos mais recentes), que caiu de 8.090 para apenas 3 páginas (-99,96% e mais de 424$\times$ de aceleração), pois a leitura reversa (`BACKWARD`) em `IX_Pedidos_DataPedido` eliminou a ordenação explícita. Também destacam-se os ganhos de sargabilidade em $Q_8$ ($114{,}0\times$) e $Q_9$ ($8{,}69\times$). Já $Q_7$ e $W_1$ são os contra-exemplos: $Q_7$ piorou em latência ($0{,}60\times$) mesmo lendo menos páginas, e $W_1$ aumentou as leituras em 85,33%."

### Slide 6 — E/S Lógica e Dispersão de Latência (07:30 – 09:00 | 1m30s)
- **Ação:** Apontar primeiro para a **Figura 1** (esquerda) e depois para os painéis (a) e (b) da **Figura 2** (direita).
- **Fala sugerida:**
  > "Os dois gráficos visualizam esse comportamento. Na Figura 1, em escala logarítmica, as consultas seletivas e ordenadas ($Q_1$–$Q_4$ e $Q_6$) reduziram entre 99,58% e 99,96% das leituras lógicas. Em $Q_8$, trocar `LIKE N'%Notebook%'` por prefixo `LIKE N'Notebook%'` (válido pela taxonomia do catálogo) cortou 95,60% das leituras; em $Q_9$, trocar `YEAR(DataPedido) = 2025` por intervalo semiaberto reduziu 80,66%. À direita, a barra vermelha de $W_1$ mostra o salto de 97 mil para 180 mil páginas na escrita.
  >
  > Na Figura 2, o painel (a) confirma a estabilidade das consultas OLTP otimizadas, todas abaixo de 1,5 ms e com variância mínima. No painel (b), $Q_5$ trocou dois *Hash Match* por *Merge Join* e *Nested Loops*, caindo de 450 para 12 ms ($37{,}5\times$), e $Q_{10}$ reescrita com `NOT EXISTS` gerou *Left Anti Semi Join* (370,5 para 219,5 ms). Em contraste, $W_1$ exibe alta dispersão, com desvio padrão de 853,2 ms. Passo a palavra ao Marcos."

---

## Integrante 4 — Marcos W. (Slides 7 e 8 | 09:00 – 12:00)

### Slide 7 — Caso $Q_4$: Eliminação de *Key Lookup* (09:00 – 10:30 | 1m30s)
- **Ação:** Percorrer as 3 barras da **Figura 3** nos painéis (a) leituras e (b) latência.
- **Fala sugerida:**
  > "Obrigado, Lizzandro. A Figura 3 mostra o experimento em três estágios da consulta $Q_4$, que filtra pedidos de uma faixa de clientes (`ClienteID BETWEEN 1000 AND 1050`) e retorna `DataPedido` e `ValorTotal`.
  >
  > No estágio 1 (*Baseline*), sem índice em `ClienteID`, o SQL Server faz *Clustered Index Scan* em todas as 8.090 páginas de `Pedidos`, levando 111 ms.
  >
  > No estágio 2, com índice simples apenas sobre `ClienteID`, o otimizador passa a fazer *Index Seek* e o tempo cai para 1 ms. Porém, como `DataPedido` e `ValorTotal` não estão no índice, o motor executa 422 operações individuais de *Key Lookup* em `PK_Pedidos`, consumindo ainda 1.296 páginas.
  >
  > No estágio 3, o índice de cobertura `IX_Pedidos_ClienteID_Cov` anexa essas duas colunas via `INCLUDE` nas folhas do índice: eliminamos *Key Lookup* e *Nested Loops*, caindo para 5 páginas (-99,94%) e menos de 1 ms."

### Slide 8 — Planos Físicos de Execução (`.sqlplan`) (10:30 – 12:00 | 1m30s)
- **Ação:** Explicar os quatro painéis (a, b, c, d) da **Figura 4** extraídos dos planos XML reais.
- **Fala sugerida:**
  > "A Figura 4 comprova essas mudanças diretamente nos planos físicos reais extraídos em XML. Nos painéis superiores: em (a), $Q_1$ substitui o *Scan* de custo estimado 2,329 por *Index Seek + Key Lookup* de custo 0,007 (6 páginas); em (b), vemos em $Q_4$ o desaparecimento do *Nested Loops* e do *Key Lookup* ao migrar do índice simples (custo 1,282) para o *Covering Index* (custo 0,004).
  >
  > Nos painéis inferiores estão as causas estruturais dos dois *trade-offs*: em (c), na consulta $Q_7$, a base *Baseline* rodava *Hash Match* em **Modo Batch**, enquanto a base otimizada mudou para *Stream Aggregate* em **Modo Row**; e em (d), na carga $W_1$, o operador *Sequence* dispara gravações síncronas em 4 árvores B+: a chave primária e os três índices secundários de `ItensPedido`. Passo a palavra ao Raildom."

---

## Integrante 5 — Raildom R. (Slides 9 e 10 | 12:00 – 15:00)

### Slide 9 — *Trade-offs* e Cache: *Warm* vs. *Cold* (12:00 – 13:45 | 1m45s)
- **Ação:** Apontar para a **Figura 5** destacando $Q_7$, $W_1$ e a comparação entre barras azuis (*Baseline*) e verdes (*Otimizado*) em *Warm* vs. *Cold*.
- **Fala sugerida:**
  > "Obrigado, Marcos. A Figura 5 compara os regimes *Warm* ($N=30$) e *Cold* ($N=10$) em escala logarítmica e explica os dois *trade-offs* centrais. Primeiro, em $Q_7$: o índice `IX_Pedidos_Status_Cov` reduziu leituras em 30,06% (8.090 para 5.658 páginas), mas o tempo subiu de 217 para 364 ms em *Warm* ($0{,}60\times$) e de 402 para 685 ms em *Cold*. O atributo `ActualExecutionMode` mostrou que, guiado pelo menor custo estimado (6,728 contra 12,640), o otimizador trocou o motor vetorizado *Batch Mode on Rowstore* pelo *Row Mode* tupla a tupla sob `MAXDOP 1`.
  >
  > Segundo, em $W_1$: atualizar quatro árvores B+ — inclusive o índice filtrado, que indexou 1.964 das 10 mil linhas inseridas — elevou as leituras em +85,33% no *Warm* e em +264,73% no *Cold Cache*, dobrando a latência de 502,0 para 1.098,5 ms ($0{,}46\times$).
  >
  > Por fim, mesmo com `physical_reads >= 1` em todas as 220 execuções frias, as consultas de leitura indexadas mantiveram forte vantagem sobre o *Baseline* frio, como $Q_1$ ($12{,}6\times$) e $Q_5$ ($4{,}33\times$)."

### Slide 10 — Conclusão e Referências (13:45 – 15:00 | 1m15s)
- **Ação:** Sintetizar conclusões e limitações, indicar as referências bibliográficas ao final e encerrar.
- **Fala sugerida:**
  > "Concluindo, nossos experimentos em 6,25 milhões de registros no SQL Server 2022 comprovam que índices B+ bem projetados e reescrita sargável reduzem leituras lógicas em até 99,96% ($Q_6$), zeram *Key Lookups* ($Q_4$) e aceleram junções e filtros em dezenas de vezes.
  >
  > Porém, os dados mostram que mais índices nem sempre significam menor latência global: cada índice secundário cobra manutenção síncrona na escrita (+85,33% em $W_1$) e decisões baseadas em custo podem perder o ganho do *Batch Mode*, elevando a latência em 67,7% ($Q_7$).
  >
  > Como limitações do estudo, registramos a execução serial com `MAXDOP 1` em container único sobre o mesmo SSD do hospedeiro, sujeito ao cache do sistema de arquivos nos testes frios. Abaixo listamos as referências que fundamentam o trabalho, incluindo Comer, Selinger, Graefe, Silberschatz, Elmasri, Ramakrishnan, Chaudhuri e a documentação oficial da Microsoft. Muito obrigado pela atenção!"
