# Decisões, pendências e riscos

## Decisões do grupo
| Decisão | Valor | Sugestão / Observação |
|---|---|---|
| Integrantes | _a definir_ | |
| SGBD | **SQL Server Developer (Docker)** | Confirmado em 13/11 (ver [comparativo-sgbds.md](../../comparativo-sgbds.md)) |
| Dataset | _a definir_ | Sintético relacional (~5–8M linhas) pelo prazo curto, ou Stack Overflow |
| Cliente gráfico (planos) | _a definir_ | Extensão `mssql` no VS Code ou SSMS |
| Idioma do paper | _a definir_ | Português |
| Análise estatística / automação | _a definir_ | Python + `uv` (já instalados na máquina) |
| Repositório de scripts | _a definir_ | Pastas locais (`docker/`, `sql/`, `scripts/`, `paper/`) no repo atual |

## Pendências a confirmar com o professor
- Tamanho do grupo (ou trabalho individual).
- Forma de submissão (e-mail, SIGAA ou outra).
- Dia da apresentação (18 ou 19/11).
- As 10 págs incluem referências? (Caber tudo em 10.)
- Perguntas contam nos 20 min? Penalidade por atraso? Entregar código/dataset?
- Critérios detalhados de nota (além do resumo em [requisitos.md](../01-requisitos/requisitos.md)).

## Próximos passos imediatos (ordem de execução)
1. Abrir o **Docker Desktop** no Windows e aguardar o motor iniciar.
2. Criar `docker-compose.yml` do SQL Server 2022 Developer (`MSSQL_PID=Developer`) e subir o container.
3. Conectar um cliente gráfico (VS Code `mssql` ou SSMS) para captura dos planos visuais.
4. Definir e carregar o dataset ($\ge 1$ milhão de linhas) sem índices secundários.
5. Baixar o template SBC em LaTeX e validar compilação com `pdflatex` (MiKTeX já instalado).
6. Executar o baseline (`Q1`–`Q10` e `W1`) com coleta automatizada (`N >= 30`) e planos salvos.

## Riscos
| Risco | Mitigação |
|---|---|
| Prazo curto (submissão 17/11 — 4 dias restantes) | Seguir o [cronograma](../03-prazos/cronograma.md) e priorizar dataset sintético |
| SGBD recusado como "comercial" | Mitigado: **SQL Server Developer** escolhido |
| Estourar 10 páginas | Compilar cedo; figuras compactas |
| Instalação/dataset demoram | Docker já instalado; dataset sintético gerado em minutos como plano principal/B |
| Limite de 10 GB do Express | Mitigado: usar edição **Developer** no container |
| Daemon do Docker parado no dia da demo | Iniciar antes; ter vídeo/prints de backup |
| Ganho imperceptível | Dataset $\ge 1$M linhas; consultas seletivas e cold/warm controlados |
