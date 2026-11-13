# Decisoes Consolidadas, Pendencias e Riscos Mitigados

## 1. Decisoes Consolidadas do Grupo
| Decisao | Definicao Final | Justificativa / Documento de Referencia |
|---|---|---|
| **SGBD** | **Microsoft SQL Server 2022 Developer Edition (Docker)** | Atende a restricao "comercial, exceto MySQL", sem limitacao de tamanho de dados e com ferramentas ricas de planos ([comparativo-sgbds.md](../../comparativo-sgbds.md)). |
| **Arquitetura de Dados** | **Duas Bases Gemeas (`Ecommerce_Baseline` e `Ecommerce_Otimizado`)** | Clonadas via `BACKUP` e `RESTORE ... WITH MOVE`. Garante grupo de controle imutavel e elimina comandos DDL durante a apresentacao oral ([plano-de-implementacao.md](../../plano-de-implementacao.md)). |
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
| Inflacao de cardinalidade no teste de escrita W1 | Media | Medio | **Mitigado:** Execucao das 30 repeticoes sob transacao revertida (`BEGIN TRAN ... ROLLBACK TRAN`). |
| Falha de ambiente no dia da apresentacao | Baixa | Fatal | **Mitigado:** Gravacao prévia de video em alta definicao da demonstracao como plano de contingencia. |
