# Artigo Cientifico (Paper <= 10 pags, Template SBC em LaTeX)

## 1. Pacote e Template Oficial da SBC
* O pacote oficial encontra-se disponivel na raiz do projeto: `SBC_Conferences_Template___updated_sbc_template_sty_v2017__1_.zip`.
* Arquivos fundamentais: `sbc-template.sty`, `sbc.bst`, `main.tex` e `sbc-template.bib`.
* Compilacao multiplataforma via script `scripts/compile_paper.py`:
  * No Windows: Suportado com MiKTeX / TeX Live (`pdflatex` e `bibtex`).
  * No Ubuntu: Suportado com TeX Live (`texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-lang-portuguese`).
* Idioma e codificacao: Pacote `babel` com opcao `brazil`, e `inputenc` com `utf8`.

---

## 2. Estrutura das Secoes e Distribuicao de Paginas (Teto Maximo: 10 Paginas)

| Secao | Conteudo Central | Orcamento de Paginas |
|---|---|---|
| **Resumo / Abstract** | Objetivos, metodologia e sintese dos speedups e reducoes de I/O | ~0,3 pag. |
| **1. Introducao** | Papel do otimizador de consultas em SGBDs relacionais corporativos e objetivos do estudo | ~0,7 pag. |
| **2. Referencial Teorico** | Arvores B+ tree, indices clustered vs nonclustered, sargabilidade, arquitetura do CBO e analise de operadores fisicos no plano de execucao | ~2,5 pags. |
| **3. Metodologia Experimental** | SGBD comercial (SQL Server 2022 Developer), isolamento com duas bases (`Ecommerce_Baseline` e `Ecommerce_Otimizado`), dataset sintetico de 6,25M tuplas (`seed=42`), leituras logicas como metrica deterministica, `MAXDOP 1` e testes estatisticos (t pareado / Wilcoxon) | ~1,5 pag. |
| **4. Resultados e Discussao** | **Tabela comparativa unificada (Q1 a Q10 e W1)**, graficos de speedup/leituras logicas, 3 a 4 figuras selecionadas de planos de execucao e analise do trade-off de escrita (W1) | ~3,5 pags. |
| **5. Conclusao** | Sintese das diretrizes praticas observadas e limitacoes conhecidas | ~0,5 pag. |
| **Referencias** | Bibliografia classica (Selinger, Graefe, Comer, Elmasri & Navathe, Silberschatz) formatada pelo `sbc.bst` | ~1,0 pag. |

---

## 3. Diretrizes Essenciais para Garantir o Limite de 10 Paginas
1. **Tabela Comparativa Unificada:** Em vez de 11 subsecoes com tabelas individuais, apresentar uma unica tabela abrangente reunindo Leituras Logicas (Antes/Depois), Reducao % (ou Overhead % para `W1`), Tempo de Execucao (Antes/Depois), Speedup (com valor `< 1,0` em `W1`) e significancia estatistica ($p < 0,001$).
2. **Selecao Visual de Planos:** Diagramar no maximo 3 a 4 figuras de arvore de operadores para os casos de maior impacto didatico:
   * Q1: *Clustered Index Scan* vs *Index Seek*;
   * Q3: Indice composto e a importancia da ordem dos predicados;
   * Q4: Eliminacao completa de *Key Lookup* comparando Baseline (*Clustered Index Scan*), indice simples (*Index Seek* + *Key Lookup*) e *Covering Index* com `INCLUDE`;
   * W1: Custo colateral de DML na manutencao de multiplas arvores B+ tree.
3. **Monitoramento Continuo:** Executar `scripts/compile_paper.py` regularmente durante a escrita para atestar ausencia de *Overfull \hbox* e conferir a contagem total de paginas no PDF resultante.

---

## 4. Estado Atual de Implementacao (Concluido em 14/11/2026)
* **Artefatos produzidos:** [main.tex](../../paper/main.tex), [sbc-template.bib](../../paper/sbc-template.bib) (8 referencias reais formatadas por `sbc.bst`), [tabela_resultados.tex](../../paper/generated/tabela_resultados.tex) e 5 figuras a 300 DPI em `paper/figures/` (`fig1_leituras_logicas.png` a `fig5_planos_execucao.png`).
* **Validacao automatica:** `uv run python scripts/compile_paper.py` gerou [main.pdf](../../paper/main.pdf) com **10 paginas exatas** (`1.311.836` bytes), `overfull_count: 0`, `undefined_warnings: []`, `bibtex_issues: []` e `"passed": true` registrados em [latex_validation.json](../../results/latex_validation.json).
* **Pendencia manual pre-submissao:** substituir o placeholder `\author{Equipe de Banco de Dados II}` pelos nomes completos e e-mails dos integrantes em `paper/main.tex` e recompilar antes de enviar ate **17/11/2026**.
