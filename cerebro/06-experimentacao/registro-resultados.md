# Registro de resultados

Preencher durante os experimentos.

## Ambiente
- **SGBD/versão:** SQL Server 2022 Developer Edition (Docker — registrar saída exata de `SELECT @@VERSION;` após subir o container)
- **Hardware/SO:** Windows 11 Home Single Language | 12th Gen Intel Core i5-1235U (10 cores / 12 threads) | 15,71 GB RAM | SSD (`KINGSTON SA400S37240G` / `SAMSUNG MZVLQ256HBJD-00B`)
- **Dataset (linhas):** E-Commerce B2C sintetico (~6,25 milhoes de registros no total: Clientes 200k, Produtos 50k, Pedidos 1,5M, ItensPedido 4,5M; seed=42)

## Resultados
| Consulta | Config. | Tempo médio (ms) | Desvio | Leituras lógicas | Operador principal | Speedup |
|---|---|---|---|---|---|---|
| Q1 | baseline | | | | | — |
| Q1 | com índice | | | | | |

## Planos capturados
(guardar imagens/XML em `06-experimentacao/planos/`)

## Observações

