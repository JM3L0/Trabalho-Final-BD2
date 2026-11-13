# Comparativo de SGBDs para o Trabalho Final de BD II

Análise técnica para escolha do SGBD considerando os requisitos do enunciado (**`Trabalho Final.pdf`**) e o prazo de entrega (**17/11/2026**).

---

## 1. Requisitos do enunciado que impactam a escolha
1. **SGBD comercial (exceto MySQL)** — exigência obrigatória.
2. **Temas obrigatórios:**
   - Utilização de índices
   - Funcionamento do plano de execução
   - Otimização de consultas
3. **Experimentos práticos** com dataset grande (milhões de registros) e resultados antes/depois no artigo.

---

## 2. Por que não usar PostgreSQL direto (sem consultar o professor)?
O **PostgreSQL** é tecnicamente excelente (`EXPLAIN (ANALYZE, BUFFERS)`, ótimo suporte a índices e gratuito), **porém é open source**, e não um SGBD comercial proprietário.

- Se o professor usou "comercial" no sentido estrito (proprietário/corporativo), o PostgreSQL pode ser rejeitado ou descontar nota.
- Se quiser usar PostgreSQL, é necessário **perguntar ao professor Dennis Sávio antes**. Sem confirmação explícita, representa risco desnecessário perto do prazo.

---

## 3. Comparação entre SGBDs comerciais (sem MySQL)

| SGBD Comercial | Facilidade de Setup | Índices e Otimização | Plano de Execução e Métricas | Veredito |
|---|---|---|---|---|
| **SQL Server Developer (via Docker ou Windows)** | **Muito fácil:** sobe com 1 comando no Docker Desktop (ou instalador Windows). Gratuito para uso acadêmico, sem limite de tamanho. | B-Tree (Clustered/Nonclustered), Covering (`INCLUDE`), Filtered, Columnstore, Views indexadas. | **Melhor da categoria:** plano gráfico no SSMS ou VS Code (`mssql`) + `SET STATISTICS IO, TIME ON` (leituras lógicas, CPU, tempo). | **Recomendado** |
| **SQL Server Express LocalDB** | **Ultra-leve:** instalador ~50 MB no Windows, sem serviço pesado. Limite de 10 GB por banco (suficiente para milhões de linhas). | Mesma engine do SQL Server. | Mesmo do SQL Server. | **Boa alternativa** se não quiser usar Docker |
| **Oracle Database 23ai Free (Docker)** | Fácil via Docker (`gvenzl/oracle-free`), gratuito (limite de 12 GB de dados). Imagem mais pesada. | B-Tree, Bitmap, Function-based, Partitioning. | `EXPLAIN PLAN` + `DBMS_XPLAN` (texto) ou gráfico no SQL Developer. | Viável, porém mais verboso e pesado |
| **IBM Db2 Community (Docker)** | Mais chato de configurar no Windows (exige flags extras no container). | Completo. | `db2exfmt` em texto (menos intuitivo). | **Descartado** (mais difícil) |
| **Cloud Data Warehouses** (Snowflake, BigQuery, Redshift) | Zero instalação (trial gratuito). | **Não usam índices B-Tree tradicionais** (usam micropartições/sort keys). | Plano focado em OLAP distribuído. | **Descartado** (não atende bem ao tema de índices) |
| **SAP HANA Express / Teradata Express** | Exigem VMs pesadas (10–16+ GB de RAM). | Colunar / MPP. | Complexo para o escopo. | **Descartado** (inviável no prazo) |
| **MongoDB** (Atlas Free / Docker) | Muito fácil (NoSQL é permitido nas sugestões do PDF). | Índices B-Tree em documentos. | `explain("executionStats")` em JSON. | Foge do foco clássico de JOINs/SQL e licença *source-available* (SSPL) pode gerar dúvida sobre ser "comercial" |

---

## 4. Conclusão

A opção com **menor atrito, menor risco e maior produtividade** é o **Microsoft SQL Server (edição Developer)** rodando no **Docker Desktop**:

1. **Conformidade total:** É inequivocamente um SGBD comercial (e não é MySQL).
2. **Setup em minutos:** Com Docker, não suja o Windows e permite resetar o ambiente facilmente.
3. **Facilita o paper e a apresentação:** O plano de execução gráfico e as métricas exatas de I/O (`logical reads`) e tempo saem prontos para virar figuras e tabelas no artigo em LaTeX, além de ficarem muito visuais na demonstração ao vivo.

