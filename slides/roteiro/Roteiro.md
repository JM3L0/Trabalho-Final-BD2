# Roteiro de Apresentação: Indexação, Planos de Execução e Otimização no SQL Server 2022

**Duração total estimada:** ~13 min 30 s (≈130 palavras/min)

| Apresentador | Slides | Conteúdo | Tempo |
|---|---|---|---|
| Hermeson | 1–3 | Abertura, introdução, fundamentação | ~2 min 30 s |
| João Marcos | 4–5 | Ambiente, bases gêmeas, índices, protocolo | ~2 min 45 s |
| Lizzandro | 6–8 | Resultados em Warm Cache, E/S e latência | ~3 min |
| Marcos | 9–10 | Caso Q4 e planos físicos | ~2 min 15 s |
| Raildom | 11–13 | Trade-offs, Warm vs. Cold, conclusão | ~3 min |

> **Legenda:** 🎤 = fala (vai para a apresentação). 📘 = apoio (**não** vai para a apresentação; serve só para dar segurança a quem fala).

---

## 1. HERMESON (slides 1, 2 e 3) — ~2 min 30 s

### Slide 1: Título

🎤 "Boa tarde a todos. Somos o grupo 5 e vamos apresentar a *Análise Experimental de Indexação, Planos de Execução e Otimização de Consultas no Microsoft SQL Server 2022*. Eu sou o Hermeson, e apresento junto com o João Marcos, o Lizzandro, o Marcos e o Raildom."

📘 **Em uma frase:** o trabalho mede, com testes reais, o quanto índices e reescrita de consultas SQL melhoram (ou pioram) o desempenho de um banco de dados.

### Slide 2: Introdução e fundamentação

🎤 "Vamos começar pelo problema. Quando um banco tem milhões de linhas, uma consulta sem índice precisa ler a tabela inteira. Isso aumenta as leituras, ocupa o *buffer pool*, que é a memória que o banco usa como cache, e atrapalha outras consultas. Isso acontece mesmo em SSD.

A solução clássica é a árvore B+, que encontra um registro em 2 a 4 acessos, mesmo com milhões de linhas. Podemos usar também a cláusula INCLUDE, que coloca colunas extras dentro do índice e evita o *Key Lookup*, uma ida extra à tabela principal. Mas há um preço: a cada escrita, todos os índices precisam ser atualizados na hora. É a *write amplification*, a amplificação de escrita.

Além dos índices, o otimizador importa. Ele só usa um índice se o filtro for *sargável*, e escolhe entre algoritmos de junção, *Nested Loops*, *Merge* e *Hash*, e entre dois modos de execução: *Batch Mode*, que processa blocos de linhas, e *Row Mode*, que processa linha a linha.

Nosso objetivo foi medir os ganhos e também os custos, os *trade-offs*, no SQL Server 2022, em uma base de 6,25 milhões de linhas, com 10 consultas de leitura, de Q1 a Q10, e uma carga de escrita, a W1, em cache quente e frio."

📘 **Termos importantes:**
- **E/S (Entrada/Saída):** leitura e escrita de páginas de dados. Cada página tem 8 KB no SQL Server. Menos páginas lidas = consulta mais barata.
- **Varredura integral (Scan):** ler a tabela inteira. É o oposto de uma busca por índice (*Seek*).
- **Buffer pool:** área da RAM onde o SQL Server guarda páginas lidas do disco. Um scan enche essa área com páginas pouco úteis e sobra menos espaço para o resto.
- **Árvore B+:** estrutura usada pelos índices. Os dados ficam nas folhas e os nós internos só guiam a busca. **O(logₘ N)** significa que o número de acessos cresce muito devagar quando N (linhas) cresce. "m" é o *fan-out* (quantos filhos cada nó tem).
- **INCLUDE / Covering Index (índice de cobertura):** índice que já contém todas as colunas pedidas pela consulta, então não precisa consultar a tabela.
- **Key Lookup:** o índice acha a linha, mas faltam colunas; o banco vai à tabela principal buscá-las. Com muitas linhas, fica caro.
- **Write amplification:** uma inserção vira várias gravações (uma por índice).
- **Predicado sargável (SARGable):** filtro escrito de modo que o índice possa ser usado. Ruim: `YEAR(DataPedido) = 2025` (função sobre a coluna). Bom: `DataPedido >= '2025-01-01' AND DataPedido < '2026-01-01'`.
- **NOT EXISTS:** forma de escrever "clientes sem pedidos". Costuma gerar um plano mais enxuto que uma subconsulta com agregação.
- **Nested Loops / Merge / Hash:** *Nested Loops* é bom para poucas linhas com índice; *Merge* é bom quando as duas entradas já estão ordenadas; *Hash* é bom para grandes volumes sem ordenação, mas usa memória.
- **Batch vs. Row Mode:** *Batch* processa centenas de linhas por vez (mais eficiente em CPU); *Row* processa uma por vez.
- **Warm vs. Cold cache:** *Warm* = dados já na memória. *Cold* = memória esvaziada, então o banco lê do disco.

### Slide 3: Divisória "Microsoft SQL Server"

🎤 "Todo o experimento foi feito no Microsoft SQL Server 2022. Agora o João Marcos explica como montamos o ambiente e o protocolo dos testes."

📘 Slide de transição. Só passar a palavra.

---

## 2. JOÃO MARCOS (slides 4 e 5) — ~2 min 45 s

### Slide 4: Metodologia, ambiente e bases gêmeas

🎤 "Obrigado, Hermeson. Os testes rodaram em um notebook com Intel Core i5 de 12ª geração, 16 GB de RAM e SSD. O SQL Server 2022 rodou em um container Docker limitado a 4 GB de RAM, e a orquestração dos testes foi feita em Python.

Criamos um esquema de e-commerce B2C com quatro tabelas: Clientes, com 200 mil linhas; Produtos, com 50 mil; Pedidos, com 1,5 milhão; e ItensPedido, com 4,5 milhões. Total: 6,25 milhões de linhas, geradas com *seed* 42, ou seja, de forma reprodutível.

A ideia central foi usar **bases gêmeas**: uma *Baseline*, só com as chaves primárias, e uma *Otimizada*, com mais 9 índices secundários. Para a comparação ser justa, garantimos paridade: atualizamos as estatísticas, verificamos que as chaves estrangeiras eram confiáveis e conferimos que as 12 estatísticas iniciais eram idênticas nas duas bases."

📘 **Termos importantes:**
- **Docker / container:** ambiente isolado onde o SQL Server roda; facilita reproduzir o experimento em outra máquina.
- **Seed 42:** semente do gerador aleatório. Com a mesma seed, os dados sintéticos saem iguais sempre.
- **Bases gêmeas:** a Baseline foi carregada primeiro; depois fez-se **BACKUP e RESTORE** para criar a cópia Otimizada, e só então os 9 índices foram criados nela. Assim, a **única diferença** entre as bases é a presença dos índices.
- **sp_updatestats:** atualiza as estatísticas (resumos da distribuição dos dados) que o otimizador usa para escolher o plano.
- **FKs confiáveis (is_not_trusted = 0):** o banco confia que as chaves estrangeiras são válidas, o que permite ao otimizador fazer simplificações.
- **Por que tanto cuidado com paridade?** Para provar que a diferença de desempenho vem dos índices, e não de estatísticas desatualizadas ou outro fator.
- **Modelo de recuperação SIMPLE (se perguntarem):** o log de transações é truncado automaticamente; reduz ruído de log nos testes.

### Slide 5: Índices secundários e protocolo

🎤 "Estes são os nove índices da base otimizada. Eles usam quatro estratégias: índices simples, como o de e-mail do cliente; índices de cobertura com INCLUDE, como o de ClienteID; um índice composto em Status e DataPedido; e um índice filtrado, que só indexa itens com desconto maior ou igual a 10. A coluna 'Alvo' mostra qual consulta cada índice atende.

No protocolo, cada cenário tem 10 consultas de leitura e uma carga de escrita, a W1, que insere 10 mil itens. A W1 roda dentro de uma transação com ROLLBACK, para que a base volte ao mesmo estado a cada medição; foram 880 execuções no total. Tudo roda com MAXDOP 1, ou seja, sem paralelismo, para isolar o efeito dos índices.

Medimos em dois regimes: *Warm*, com 30 repetições, e *Cold*, com 10 repetições após limpar a memória. Na estatística, usamos o teste de Shapiro-Wilk para verificar se os dados são normais e, conforme o resultado, o teste t pareado ou o de Wilcoxon."

📘 **Termos importantes:**
- **Índice simples:** uma coluna só (ex.: Email).
- **Índice composto (Status, DataPedido):** a ordem das colunas importa. Serve para "igualdade em Status + intervalo em DataPedido".
- **Índice filtrado:** índice com `WHERE`, que guarda só um subconjunto das linhas (aqui, Desconto >= 10, cerca de 20% dos itens). É menor e mais barato de manter.
- **ROLLBACK:** desfaz a inserção. Mantém sempre 4,5 milhões de linhas em ItensPedido.
- **880 execuções:** não precisa decorar o cálculo; basta dizer que é o total de medições do protocolo.
- **MAXDOP 1:** *Max Degree of Parallelism* = 1; a consulta usa um único núcleo. Evita que o paralelismo "misture" o efeito do índice com o efeito de threads. Também é uma **limitação** do estudo.
- **Warm (N = 30):** 30 repetições pareadas, com 2 aquecimentos descartados.
- **Cold (N = 10):** antes de cada execução se esvazia o buffer pool e o cache de planos (`DBCC DROPCLEANBUFFERS`, `DBCC FREEPROCCACHE`).
- **Shapiro-Wilk:** testa se as diferenças seguem distribuição normal. Se sim, **t pareado**; se não, **Wilcoxon** (não paramétrico).
- **Valor p:** probabilidade de o resultado ter ocorrido por acaso. **p < 10⁻⁴** = diferença estatisticamente muito forte.

---

## 3. LIZZANDRO (slides 6, 7 e 8) — ~3 min

### Slide 6: Resultados em Warm Cache

🎤 "Obrigado, João Marcos. Vamos aos resultados em cache quente. Esta tabela mostra, para cada consulta, as leituras lógicas, o tempo e o *speedup*, que é quantas vezes ficou mais rápido.

Em 9 das 10 consultas de leitura, a melhora foi estatisticamente significativa, com p menor que 10 elevado a menos 4. O maior ganho foi na Q6: as leituras caíram de 8.090 para 3 páginas, e o speedup passou de 424 vezes. Isso aconteceu porque o índice permite ler os dados já ordenados, no sentido inverso, sem precisar do operador Sort.

A sargabilidade também teve impacto. Na Q8, trocar um curinga no início do texto por uma busca por prefixo deu um speedup de 114 vezes. Na Q9, trocar a função YEAR por um intervalo semiaberto deu 8,69 vezes.

Mas há contra-exemplos. A Q7 ficou mais lenta, com speedup de 0,60, e a escrita W1 aumentou as leituras em 85,33%. Essas duas exceções o Raildom explica mais adiante."

📘 **Termos importantes:**
- **Leitura lógica:** página de 8 KB lida do buffer pool. É a métrica de E/S usada.
- **Speedup:** tempo base ÷ tempo otimizado. **0,60× significa que ficou mais lento** (cerca de 1,67 vez mais lento).
- **Mediana:** os tempos são medianos, o que é mais robusto contra valores extremos.
- **"< 1 ms":** o cronômetro do SQL Server tem precisão de 1 ms; tempos abaixo de 0,5 ms aparecem como 0. Por isso Q1, Q4 e Q6 aparecem como "< 1 ms" e o speedup é calculado como **piso conservador** (o real é pelo menos aquele valor).
- **Q6 (TOP 50 mais recentes):** o índice em DataPedido, lido em ordem inversa (**BACKWARD**), entrega os 50 últimos pedidos sem **Sort** explícito.
- **Q8 (prefixo):** `LIKE 'Notebook%'` usa Seek; `LIKE '%Notebook%'` obriga a varrer tudo. A reescrita só funciona porque os nomes seguem uma taxonomia; para termos em posições quaisquer, o recomendado seria **Full-Text**.
- **Q9 (intervalo semiaberto):** `>= '2025-01-01' AND < '2026-01-01'` permite Index Seek; `YEAR(coluna) = 2025` não.
- **Q7 e W1 (as duas exceções):** deixe a explicação para o Raildom; aqui basta mencionar.

### Slide 7: E/S lógica (Figura 1)

🎤 "Este gráfico mostra as leituras lógicas em escala logarítmica. As barras azuis são a base *Baseline* e as verdes, a otimizada. Em Q1 a Q4 e Q6, as quedas ficam entre 99,58% e 99,96%. Já a barra vermelha, a W1, mostra o contrário: a escrita passou de cerca de 97 mil para 180 mil páginas."

📘 **Termos importantes:**
- **Escala logarítmica:** cada marca no eixo é 10 vezes maior que a anterior. Sem ela, as barras de 3 ou 6 páginas seriam invisíveis ao lado de 8.090.
- **Cuidado ao falar:** o gráfico mostra **E/S**, não tempo.
- **Barra vermelha:** simboliza o *overhead* de escrita.

### Slide 8: Dispersão de latência (Figura 2)

🎤 "Aqui vemos a dispersão dos tempos, em *boxplots*. No painel (a), nas consultas de busca seletiva, as versões otimizadas ficam estáveis, em no máximo 1,5 ms, com dispersão mínima. No painel (b), vemos as consultas analíticas: a Q5 melhorou 37,5 vezes com *Merge* e *Nested Loops*, e a Q10, com NOT EXISTS, 1,69 vez. Repare na W1: a caixa vermelha é bem larga, com desvio-padrão de 853 ms, ou seja, a escrita com mais índices é bem menos previsível."

📘 **Termos importantes:**
- **Boxplot:** a caixa mostra onde estão 50% dos valores; a linha no meio é a mediana; os "bigodes" mostram a faixa geral; os pontinhos são *outliers*. **Caixa grande = muita variação.**
- **Desvio-padrão (DP):** mede a dispersão. DP de 853,2 ms na W1 é muito maior que a mediana (404 ms).
- **Q5 (junção de 3 tabelas):** o Baseline fazia dois *Hash Match* sobre scans completos (28.818 páginas). Com índices, passou a usar *Merge Join* + *Nested Loops* com busca indexada (5.295 páginas).
- **Q10 (NOT EXISTS):** a subconsulta correlacionada com agregação virou um *Left Anti Semi Join* (retorna só quem **não** tem correspondência).
- **Se perguntarem sobre W1 p = 0,129:** em Warm, a diferença de tempo da W1 **não** foi significativa; o que é significativo é o aumento de E/S. Em Cold, p = 0,00195.

---

## 4. MARCOS (slides 9 e 10) — ~2 min 15 s

### Slide 9: Caso Q4, eliminação de Key Lookup

🎤 "Obrigado, Lizzandro. Agora um estudo de caso: a Q4, que busca pedidos de clientes com ID entre 1000 e 1050. Dividimos em três estágios para isolar o custo do *Key Lookup*.

No primeiro, a *Baseline*, o banco faz um *Clustered Index Scan*: 8.090 páginas e 111 ms.

No segundo, criamos um índice simples em ClienteID. Agora o banco faz um *Index Seek*, mas ainda precisa de 422 *Key Lookups*, um para cada linha, para buscar DataPedido e ValorTotal. Resultado: 1.296 páginas e cerca de 1 ms.

No terceiro, criamos o índice de cobertura, com INCLUDE de DataPedido e ValorTotal. Todas as informações já estão no índice, então o Lookup e o *Nested Loops* desaparecem: apenas 5 páginas, menos de 1 ms, uma redução de 99,94%."

📘 **Termos importantes:**
- **Por que três estágios?** Para mostrar que o índice simples já ajuda muito (8.090 → 1.296), mas só o **INCLUDE** elimina o custo restante (1.296 → 5). Assim se isola o custo do Key Lookup.
- **Clustered Index Scan:** varre a tabela inteira (a tabela *é* o índice clusterizado).
- **Index Seek:** navega na árvore B+ direto até o ponto desejado.
- **Key Lookup:** para cada linha achada no índice, uma busca extra na tabela principal pela chave primária. 422 linhas = 422 lookups.
- **Nested Loops:** junção que combina o resultado do Seek com os Lookups; some junto quando o Lookup some.
- **Atenção:** o estágio intermediário tem latência de ~1 ms, mas isso é por causa do pouco volume de dados; o ponto principal do estágio é o **número de páginas**.

### Slide 10: Planos físicos de execução (.sqlplan)

🎤 "Estes são os planos físicos extraídos dos arquivos .sqlplan, em quatro painéis. Nos painéis (a) e (b), vemos busca e cobertura. Na Q1, o *Scan* completo, de custo estimado 2,329, é trocado por um *Seek* mais um *Lookup*, de custo 0,007. Na Q4, o índice de cobertura remove o Lookup e o custo cai para 0,004.

Os painéis (c) e (d) mostram os trade-offs. Na Q7, o plano passa de *Hash Match* em *Batch Mode* para *Stream Aggregate* em *Row Mode*. E na W1, a inserção grava em quatro árvores B+ ao mesmo tempo, dentro de um operador *Sequence*. O Raildom vai explicar o que isso significa na prática."

📘 **Termos importantes:**
- **.sqlplan:** arquivo XML do plano de execução real, gerado com `SET STATISTICS XML ON`.
- **Custo estimado:** valor interno do otimizador (unidade abstrata, não é tempo). **Atenção:** custo menor **nem sempre** significa tempo menor; a Q7 é o exemplo.
- **Hash Match [Aggregate] / Batch:** agrega usando tabela hash, processando blocos de linhas.
- **Stream Aggregate / Row:** agrega lendo dados já ordenados, linha a linha.
- **Sequence (W1):** operador que executa várias gravações em sequência: o índice clusterizado + 2 índices secundários + o filtrado = **4 árvores B+**.
- **Custo da W1 (3,841):** não precisa citar; basta dizer que são 4 inserções por linha.

---

## 5. RAILDOM (slides 11, 12 e 13) — ~3 min

### Slide 11: Trade-offs e cache, Warm vs. Cold

🎤 "Obrigado, Marcos. Vamos aos dois comportamentos mais interessantes do estudo.

O primeiro é a **inversão em Q7**. O índice reduziu as leituras em 30%, mas a latência *piorou*: de 217 para 364 ms em cache quente, speedup de 0,60, e de 402 para 685 ms em cache frio. A causa está no plano: na base original, o otimizador usava *Hash Match* em *Batch Mode*, que processa blocos de linhas. Na base otimizada, como o custo estimado era menor, ele escolheu um *Stream Aggregate* em *Row Mode*, linha a linha, com mais CPU sob MAXDOP 1. Ou seja, menos páginas lidas não garantiu menos tempo.

O segundo é a **amplificação de escrita na W1**. Cada linha inserida precisa atualizar quatro árvores B+. As leituras subiram 85,33% em cache quente e 264,73% em cache frio. Em cache frio, o tempo foi de 502 ms para 1.098 ms, speedup de 0,46.

Por fim, no **cache frio**, todas as 220 execuções tiveram leitura física, confirmando que os dados vieram do disco. Os tempos subiram, mas as consultas de leitura mantiveram o ganho: 12,6 vezes na Q1 e 4,33 vezes na Q5."

📘 **Termos importantes:**
- **Por que Q7 piorou?** O otimizador usa **custo estimado**, e o plano de Row Mode parecia mais barato (6,728 vs. 12,640). Mas o **Batch Mode** é muito mais eficiente em CPU para agregar 1,5 milhão de linhas. O plano "mais barato no papel" foi mais lento na prática.
- **Aumento de 67,7% (slide 12):** (364 − 217) ÷ 217 ≈ 67,7% de latência a mais.
- **Atenção às duas formas de dizer a mesma coisa:** speedup 0,60× ≈ latência +67,7%. Não são dois resultados diferentes.
- **W1 Warm vs. Cold:** Warm = 97.154 → 180.057 leituras (+85,33%). Cold = 77.448,5 → 282.476 (+264,73%).
- **Q1 e Q5 em Cold:** Q1 foi de 44 ms (base fria) para 3,5 ms; Q5, de 1.027,5 ms para 237,5 ms. O tempo da Q5 otimizada subiu de 12 ms para 237,5 ms por causa de acesso aleatório a páginas frias em ItensPedido.
- **physical_reads >= 1:** leitura física = ida ao disco. Prova que o cache foi mesmo esvaziado.
- **Cold Cache e limitação:** o experimento rodou no mesmo SSD do host, então o **cache do sistema operacional** pode ter suavizado um pouco o efeito.

### Slide 12: Conclusão

🎤 "Para concluir. Primeiro, os índices e a reescrita de consultas trouxeram ganhos expressivos na leitura: até 99,96% menos E/S, fim dos Key Lookups na Q4 e aceleração em junções e em predicados sargáveis, nas consultas Q5, Q8 e Q9.

Segundo, **mais índices não significam menor latência**. A manutenção síncrona encarece a escrita, com +85,33% de E/S na W1, e um custo estimado menor pode fazer o otimizador perder o Batch Mode, como na Q7, com 67,7% a mais de latência.

Por fim, as limitações: execução serial com MAXDOP 1, em um único container, no mesmo SSD do computador, sujeito ao cache do sistema operacional nos testes frios. Como trabalhos futuros, sugerimos testar paralelismo, índices colunares e cargas concorrentes de leitura e escrita."

📘 **Termos importantes:**
- **Mensagem-chave (decorar):** "Índice não é de graça: ele acelera leitura, mas encarece escrita, e o otimizador nem sempre escolhe o melhor plano."
- **Columnstore (trabalho futuro):** índice armazenado por colunas, ideal para agregações analíticas como a Q7.
- **Cargas concorrentes:** leituras e escritas ao mesmo tempo, o que não foi testado.

### Slide 13: Referências

🎤 "Essas são as referências do trabalho. Agradecemos a atenção de todos e estamos à disposição para perguntas."

📘 **Possíveis perguntas e respostas curtas:**

| Pergunta provável | Resposta curta |
|---|---|
| Por que usar MAXDOP 1? | Para isolar o efeito dos índices e evitar ruído de paralelismo no container; é uma limitação reconhecida. |
| Por que a Q7 ficou mais lenta? | O otimizador escolheu um plano de menor custo estimado, mas em Row Mode; o plano original usava Batch Mode, mais eficiente em CPU. |
| Vale criar todos os índices possíveis? | Não: cada índice custa espaço e encarece escritas (W1 +85,33% de E/S). Deve-se indexar conforme a carga de trabalho. |
| Como garantiram uma comparação justa? | Bases gêmeas via BACKUP/RESTORE, estatísticas idênticas, FKs confiáveis, mesmo hardware e ordem alternada de execução. |
| O que é sargabilidade? | Escrever o filtro de modo que o índice possa ser usado, sem funções sobre a coluna e sem curinga no início. |
| Por que testar Warm e Cold? | Warm mostra o custo de CPU/lógico; Cold inclui o custo de ler do disco. Os ganhos de leitura se mantiveram nos dois. |
| Por que os resultados valem só para este cenário? | Foram 6,25 milhões de linhas, dados sintéticos, um único SGBD e um único container; os resultados indicam tendências, não regras universais. |

---

## Dicas gerais para o grupo

- **Transições:** ao terminar, cada pessoa cita o próximo ("Agora o Lizzandro...") para a troca ficar fluida.
- **Tempo:** ensaiem cronometrando; a fala de cada um está calibrada para ~130 palavras/min. Se passar de 15 min, cortem os detalhes de Cold Cache do slide 11.
- **Números para decorar:** 6,25M linhas · 9 índices · Q6: 8.090 → 3 págs (424×) · Q4: 8.090 → 1.296 → 5 págs · Q7: 0,60× · W1: +85,33% (Warm) e +264,73% (Cold).