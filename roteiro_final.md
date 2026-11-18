# Roteiro de Apresentação: Indexação, Planos de Execução e Otimização no SQL Server 2022

**Duração estimada de fala:** ~9 min 30 s (ritmo de ~130 palavras/min), deixando ~2 min de folga para trocas de apresentador dentro dos 12 min.

| Apresentador | Slides | Conteúdo | Tempo |
|---|---|---|---|
| Raildom | 1–3 | Abertura, introdução, SQL Server | ~1 min 35 s |
| João Marcos | 4–6 | Ambiente, bases gêmeas, índices, protocolo | ~1 min 55 s |
| Marcos | 7 | Consultas por grupo | ~1 min 05 s |
| Lizzandro | 8–9 | Resultados em Warm Cache e E/S | ~1 min 35 s |
| Hermeson | 10–11 | Planos físicos e trade-offs | ~1 min 45 s |
| Marcos | 12–13 | Conclusão e referências | ~1 min 10 s |

**Estrutura dos slides**

1. Título
2. Introdução e fundamentação
3. Microsoft SQL Server 2022 *(novo)*
4. Ambiente *(Tabela 1)*
5. Bases gêmeas *(dados e paridade; resultado da divisão do slide original)*
6. Índices secundários e protocolo
7. Consultas: Baseline vs. Otimizado *(novo, tabela por grupo)*
8. Resultados em Warm Cache (Tabela 3)
9. E/S lógica em Warm Cache (Figura 1)
10. Planos físicos de execução (.sqlplan), imagem inteira
11. Trade-offs e cache: Warm vs. Cold
12. Conclusão
13. Referências

> **Removidos em relação ao original:** divisória "Microsoft SQL Server" (substituída pelo slide 3), boxplot (Fig. 2) e Caso Q4.

---

## 1. RAILDOM (slides 1, 2 e 3)

### Slide 1: Título

"Boa tarde a todos. Somos o grupo 5 e vamos apresentar uma análise experimental de indexação, planos de execução e otimização de consultas no SQL Server 2022. Eu sou o Hermeson, e apresento com o João Marcos, o Lizzandro, o Marcos e o Raildom."

### Slide 2: Introdução e fundamentação

"Em bancos com milhões de linhas, uma consulta sem índice precisa ler a tabela inteira. Isso acontece mesmo em SSD, e pesa no desempenho de todo o sistema.

A solução clássica são os índices em árvore B+, que encontram um registro em poucos acessos. Mas isso tem um preço: toda escrita precisa atualizar todos os índices.

Por isso, nosso objetivo foi medir os dois lados: quanto os índices e a reescrita de consultas ganham, e quanto custam. Fizemos isso em uma base de 6,25 milhões de linhas. Vamos ver como isso funciona no SQL Server."

### Slide 3: Microsoft SQL Server 2022

"Todo o experimento foi feito no Microsoft SQL Server 2022. Ele usa um otimizador baseado em custo: para cada consulta, gera um plano de execução, uma sequência de operadores como Scan, Seek e junções, e escolhe o de menor custo estimado. O motor também pode processar em blocos de linhas, o Batch Mode, ou linha a linha, o Row Mode. Esse detalhe vai importar nos resultados. Agora o João Marcos mostra como montamos o experimento."

---

## 2. JOÃO MARCOS (slides 4, 5 e 6)

### Slide 4: Ambiente e bases gêmeas (parte 1: ambiente)

"Obrigado, Hermeson. Os testes rodaram em um notebook com Core i5, 16 GB de RAM e SSD, com o SQL Server 2022 em um container Docker de 4 GB."

### Slide 5: Ambiente e bases gêmeas (parte 2: dados e bases gêmeas)

"Criamos um banco de e-commerce com quatro tabelas e 6,25 milhões de linhas, geradas de forma reprodutível.

A ideia central foram as bases gêmeas: uma Baseline, só com chaves primárias, e uma Otimizada, com nove índices a mais. Garantimos que as estatísticas e as chaves estrangeiras fossem idênticas nas duas, para que a única diferença fossem os índices."

### Slide 6: Índices secundários e protocolo

"Os nove índices seguem quatro estratégias: simples, de cobertura com INCLUDE, composto e filtrado. O INCLUDE coloca colunas extras dentro do índice, para a consulta não precisar voltar à tabela principal. Esse retorno se chama Key Lookup.

Cada cenário tem dez consultas de leitura e uma carga de escrita, a W1, que insere dez mil linhas. Medimos em cache quente, com 30 repetições, e em cache frio, com 10, após limpar a memória. Tudo rodou sem paralelismo, com MAXDOP 1, para isolar o efeito dos índices. Na estatística, usamos o teste t pareado ou o de Wilcoxon. Agora o Marcos apresenta as consultas."

---

## 3. MARCOS (slide 7)

### Slide 7: Consultas: Baseline vs. Otimizado

"Para facilitar os resultados, agrupamos as consultas em quatro blocos.

O primeiro são as buscas seletivas, de Q1 a Q4 e a Q6: na base original, o banco varre a tabela inteira; na otimizada, vai direto ao ponto pelo índice, e a Q6 ainda lê os dados já ordenados, sem precisar ordenar.

O segundo são junção e agregação, Q5 e Q7. A Q5 troca dois Hash Match por Merge Join e Nested Loops. A Q7 é uma exceção que o Raildom explica.

O terceiro são as reescritas de SQL, de Q8 a Q10: curinga no início virou prefixo, a função YEAR virou intervalo de datas, e a subconsulta virou NOT EXISTS.

Por fim, a escrita, W1: de uma árvore B+ para quatro. Agora o Lizzandro apresenta os resultados."

---

## 4. LIZZANDRO (slides 8 e 9)

### Slide 8: Resultados em Warm Cache

"Obrigado, Marcos. Em cache quente, nove das dez consultas de leitura melhoraram de forma estatisticamente significativa.

O maior ganho foi a Q6: as leituras caíram de 8.090 para 3 páginas, mais de 400 vezes mais rápida, porque o índice entrega os dados já ordenados.

As reescritas também funcionaram: o prefixo na Q8 deu 114 vezes, e o intervalo de datas na Q9, quase 9 vezes.

Nas buscas por cobertura, o índice eliminou o Key Lookup: o retorno à tabela principal desapareceu."

### Slide 9: E/S lógica em Warm Cache

"O gráfico mostra o mesmo em E/S, em escala logarítmica: quedas de 99% nas buscas seletivas. Mas a barra vermelha, a escrita W1, vai no sentido oposto: de 97 mil para 180 mil páginas lidas. Essa e a Q7, que ficou mais lenta, são as exceções. O Raildom mostra agora os planos por trás delas."

---

## 5. HERMESON (slides 10 e 11)

### Slide 10: Planos físicos de execução (.sqlplan), imagem inteira

> **Animação:** 4 retângulos de destaque (a, b, c, d), um clique por painel, na ordem da fala. Os cliques estão marcados com **[clique]**.

"Obrigado, Lizzandro. Estes são os planos reais extraídos do SQL Server. Em cima, os ganhos: **[clique 1]** na Q1, o Scan completo vira um Seek no índice, e **[clique 2]** na Q4, o índice de cobertura elimina o Key Lookup. Embaixo, os trade-offs. **[clique 3]** Na Q7, o otimizador trocou o Hash Match em Batch Mode por um Stream Aggregate em Row Mode, porque o custo estimado era menor, mas linha a linha usa mais CPU. **[clique 4]** E na W1, cada linha inserida grava em quatro árvores B+ ao mesmo tempo. Agora, os números."

### Slide 11: Trade-offs e cache: Warm vs. Cold

"Na Q7, o índice reduziu as leituras em 30%, mas a latência subiu de 217 para 364 milissegundos em cache quente, e de 402 para 685 em cache frio. Como vimos no plano, o otimizador escolheu o plano mais barato no papel, mas mais lento na prática. Menos páginas lidas não garantiu menos tempo.

Na W1, as leituras subiram 85% em cache quente e 265% em cache frio.

No cache frio, os tempos aumentam, pois os dados vêm do disco, mas os ganhos de leitura se mantêm. Agora o Marcos conclui."

---

## 6. MARCOS (slides 12 e 13)

### Slide 12: Conclusão

"Para concluir. Primeiro, índices e reescrita trouxeram ganhos expressivos na leitura: até 99,96% menos E/S, fim dos Key Lookups e melhora em junções e filtros sargáveis.

Segundo, mais índices não significam menor latência: a escrita ficou mais cara, e um custo estimado menor levou a um plano pior na Q7.

Como limitações, usamos MAXDOP 1, um único container e o mesmo SSD do computador. Como trabalhos futuros, sugerimos paralelismo, índices colunares e cargas concorrentes.

A mensagem final: índice não é de graça. Ele acelera a leitura, encarece a escrita, e o otimizador nem sempre escolhe o melhor plano."

### Slide 13: Referências

"Estas são as referências. Obrigado a todos, estamos à disposição para perguntas."

---

## Apoio (não vai para a apresentação)

### Se o tempo apertar, corte nesta ordem

1. Cold Cache no slide 11 (último parágrafo do Raildom).
2. Frase do teste t pareado/Wilcoxon no slide 6.
3. Reescritas (Q8 e Q9) na fala do slide 8.

### Números para decorar

6,25M linhas · 9 índices · Q6: 8.090 → 3 páginas (424×) · Q7: 217 → 364 ms (0,60×) · W1: +85,33% (Warm) e +264,73% (Cold)

### Possíveis perguntas e respostas curtas

| Pergunta | Resposta curta |
|---|---|
| Por que MAXDOP 1? | Para isolar o efeito dos índices e evitar ruído de paralelismo no container. É uma limitação reconhecida. |
| Por que a Q7 ficou mais lenta? | O otimizador escolheu um plano de menor custo estimado, mas em Row Mode. O plano original usava Batch Mode, mais eficiente em CPU. |
| Vale criar todos os índices possíveis? | Não. Cada índice custa espaço e encarece escritas (W1 +85,33% de E/S). Deve-se indexar conforme a carga de trabalho. |
| Como garantiram uma comparação justa? | Bases gêmeas via BACKUP/RESTORE, estatísticas idênticas, chaves estrangeiras confiáveis, mesmo hardware e ordem alternada de execução. |
| O que é sargabilidade? | Escrever o filtro de modo que o índice possa ser usado: sem funções sobre a coluna e sem curinga no início. |
| Por que testar Warm e Cold? | Warm mostra o custo lógico e de CPU. Cold inclui a leitura do disco. Os ganhos de leitura se mantiveram nos dois. |
| Por que a diferença de tempo da W1 em Warm não é significativa? | Em Warm, p = 0,129. O resultado robusto é o aumento de E/S. Em Cold, p = 0,00195. |
| Por que os resultados valem só para este cenário? | Dados sintéticos, 6,25M linhas, um SGBD e um container. Indicam tendências, não regras universais. |

### Dicas gerais

- **Transições:** cada pessoa cita o próximo apresentador no fim da fala.
- **Ensaio:** cronometrem. Se passar de 11 min no ensaio, apliquem os cortes acima.
- **Slide 10:** ensaiem os cliques junto com a fala, para o destaque aparecer na palavra certa.