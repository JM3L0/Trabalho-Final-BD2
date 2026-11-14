# Decisoes Consolidadas, Pendencias e Riscos Mitigados

## 1. Decisoes Consolidadas do Grupo
| Decisao | Definicao Final | Justificativa / Documento de Referencia |
|---|---|---|
| **SGBD** | **Microsoft SQL Server 2022 Developer Edition (Docker)** | Atende a restricao "comercial, exceto MySQL", sem limitacao de tamanho de dados e com ferramentas ricas de planos ([comparativo-sgbds.md](../06-experimentacao/comparativo-sgbds.md)). |
| **Arquitetura de Dados** | **Duas Bases Gemeas (`Ecommerce_Baseline` e `Ecommerce_Otimizado`)** | Clonadas via `BACKUP` e `RESTORE ... WITH MOVE`. Garante grupo de controle imutavel e elimina comandos DDL durante a apresentacao oral ([plano-de-implementacao.md](../02-planejamento/plano-de-implementacao.md)). |
| **Dataset** | **E-Commerce B2C Sintetico (~6,25M linhas)** | Tabelas `Clientes` (200k), `Produtos` (50k), `Pedidos` (1,5M) e `ItensPedido` (4,5M). Semente pseudoaleatoria fixa (`seed=42`) para 100% de reprodutibilidade. |
| **Compatibilidade** | **Multiplataforma (Windows e Ubuntu Linux)** | Docker Compose com volumes POSIX relativos, Python gerenciado por `uv`, driver `pymssql` com FreeTDS embutido, `pathlib.Path` e `.gitattributes`. |
| **Template do Paper** | **Template Oficial SBC em LaTeX** | Pacote extraido de `SBC_Conferences_Template___updated_sbc_template_sty_v2017__1_.zip`, compilado via script `scripts/compile_paper.py`. |
| **Idioma do Artigo** | **Portugues** | Conforme padrao usual da SBC e da disciplina. |
| **Cliente Grafico** | **VS Code (`mssql`), Azure Data Studio ou SSMS** | Extensoes multiplataforma que geram os diagramas de planos de execucao e exportam XML. |

---

## 2. Pendencias a Confirmar com o Docente
* Confirmar se as 10 paginas do artigo incluem as referencias bibliograficas (planejamento atual assume que o teto total inclui referencias).
* Confirmar se o tempo de arguicao da banca esta incluso nos 20 minutos de apresentacao.
* Canal oficial de envio do PDF final (SIGAA ou e-mail).

---

## 3. Matriz de Riscos e Mitigacoes Validadas

| Risco Identificado | Probabilidade | Impacto | Estrategia de Mitigacao Adotada |
|---|---|---|---|
| Incompatibilidade de SGBD com o enunciado | Baixa | Fatal | **Mitigado:** SQL Server Developer e inequivocamente comercial proprietario. |
| Estouro do limite maximo de 10 paginas | Alta | Medio | **Mitigado:** Sintese das consultas Q1 a Q10 e W1 em tabela comparativa unificada; limitacao de 3 a 4 figuras de planos graficos no paper. |
| Travamento ou atraso na demo ao vivo de 20 min | Alta | Alto | **Mitigado:** Uso de duas bases pre-indexadas (`Ecommerce_Baseline` e `Ecommerce_Otimizado`), executando consultas lado a lado sem rodar DDL na apresentacao. |
| Explosao do arquivo de log (.ldf) na carga massiva | Media | Alto | **Mitigado:** Configuracao de `RECOVERY SIMPLE` e parametrizacao de `BATCHSIZE = 100000` no `BULK INSERT`. |
| Falha de permissao no Ubuntu (UID 10001 do container) | Media | Alto | **Mitigado:** Comando de setup `chmod -R 777 ./data` (leitura dos CSVs e escrita do backup `.bak`) e arquivos com permissao `0644`. |
| Quebra de scripts no Linux por terminadores CRLF | Media | Medio | **Mitigado:** Configuracao de `.gitattributes` com `eol=lf` para scripts shell e Python. |
| Variancia estatistica de CPU nos testes | Media | Baixo | **Mitigado:** Fixacao de `OPTION (MAXDOP 1)` e uso de Leituras Logicas como metrica deterministica primaria. |
| Inflacao de cardinalidade no teste de escrita W1 | Media | Medio | **Mitigado:** Execucao das 30 repeticoes sob transacao revertida (`BEGIN TRAN ... ROLLBACK TRAN`), capturando `STATISTICS IO, TIME` apenas do `INSERT` antes do `ROLLBACK`. |
| Plano real divergir do esperado (ex.: Q7 dar Hash ou Q10 igualar planos) | Media | Medio | **Mitigado:** Validacao previa (`1x` com `SET STATISTICS XML ON`) em ambas as bases antes da bateria $N \ge 30$; uso de *Covering Index* em Q7 e validacao de nulabilidade/correlacao em Q10. |
| Lentidao na geracao dos CSVs ou na bateria Cold Cache | Media | Medio | **Mitigado:** Geracao vetorizada com `numpy`; bateria principal $N \ge 30$ em *Warm Cache* + *Cold Cache* calibrado; separacao entre captura XML (1x) e loop estatistico. |
| Atraso na redacao do paper (70% da nota) ate 17/11 | Media | Alto | **Mitigado:** Artigo [main.pdf](../../paper/main.pdf) concluido em 14/11 com 10 paginas exatas e aprovado por validacao automatica e auditorias. |
| Falha de ambiente no dia da apresentacao | Baixa | Fatal | **Mitigado parcialmente:** Plano B pronto ([README_CONTINGENCIA.md](../../scripts/demo/README_CONTINGENCIA.md) + 23 arquivos `.sqlplan` em `results/plans/`); falta apenas a equipe gravar localmente `slides/demo_backup_local.mp4` antes da banca. |
