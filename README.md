# Trabalho Final — Banco de Dados II (UFPI 2026.2)

Experimentos praticos de indexacao, planos de execucao e otimizacao de consultas no **Microsoft SQL Server 2022 Developer Edition** (Docker), com analise estatistica em Python (`uv`) e artigo cientifico no template da SBC (`LaTeX`).

## Setup do Ambiente (Parte 1.1 — Docker Multiplataforma)

1. *(Opcional)* Copie `.env.example` para `.env` e ajuste a senha/porta local:
   ```bash
   cp .env.example .env
   ```
2. **No Ubuntu Linux**, garanta as permissoes de leitura/escrita em `./data` para o usuario do container (`uid 10001`):
   ```bash
   bash scripts/setup_ubuntu.sh
   # ou manualmente: mkdir -p ./data && chmod -R 777 ./data
   ```
3. Suba o container do SQL Server 2022 Developer:
   ```bash
   docker compose up -d --wait
   ```
4. Valide a instancia:
   ```bash
   docker exec bd2_sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "Bd2Trabalho!2026" -C -Q "SELECT @@VERSION;"
   ```

## Ferramental de Analise e Planos Graficos (Parte 1.2)

O repositorio inclui `.vscode/extensions.json` e `.vscode/settings.json` pre-configurados com perfis de conexao para `Ecommerce_Baseline` e `Ecommerce_Otimizado` usando a extensao oficial **`SQL Server (mssql)`** (`ms-mssql.mssql`), compativel com Windows e Ubuntu (ou alternativamente via Azure Data Studio).

* **Visualizacao grafica do plano:** Na barra de resultados do VS Code (`mssql`), ative **Enable Actual Plan (MSSQL)** (`mssql.enableActualPlan`, apos criar as bases na Parte 2, ou execute `SET STATISTICS XML ON;` e abra o `.sqlplan` resultante).
* **Metricas de I/O e tempo:** Execute `SET STATISTICS IO, TIME ON;` antes da consulta para inspecionar `logical reads`, `CPU time` e `elapsed time` na aba *Messages*.

## Orquestracao em Python via `uv` (Parte 1.3)

Todos os scripts utilizam `uv`, `pathlib.Path` e o driver `pymssql` (FreeTDS embutido, sem necessidade de drivers ODBC externos).

```bash
uv sync
uv run python scripts/smoke_test.py
```

## Compilacao do Artigo LaTeX SBC (Parte 1.4)

O template oficial da SBC esta descompactado em `paper/`.

* **Windows:** MiKTeX ou TeX Live (`pdflatex` e `bibtex` no `PATH`).
* **Ubuntu:** `sudo apt install texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-lang-portuguese`.
* **Compilar:**
  ```bash
  uv run python scripts/compile_paper.py
  ```



