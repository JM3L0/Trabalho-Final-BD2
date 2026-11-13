# Plano de consultas (a refinar após definir dataset)

| ID | Tipo | Otimização testada | Índice/técnica |
|---|---|---|---|
| Q1 | Igualdade em coluna não indexada | Índice simples | Index Seek vs Scan |
| Q2 | Faixa (BETWEEN/datas) | Índice em data | Range seek |
| Q3 | Igualdade + faixa | Índice composto (ordem das colunas) | Composto |
| Q4 | SELECT de poucas colunas | Covering/INCLUDE | Elimina lookup |
| Q5 | JOIN de 2–3 tabelas | Índice em FK | Troca de Hash por Nested Loops |
| Q6 | ORDER BY / TOP | Índice ordenado | Elimina Sort |
| Q7 | GROUP BY / agregação | Índice/ view indexada | Stream Aggregate |
| Q8 | `LIKE '%x'` vs `'x%'` | Sargabilidade | — |
| Q9 | Função em coluna no WHERE | Reescrita | Sargable |
| Q10 | Subconsulta correlacionada | Reescrita com JOIN/EXISTS | — |
| W1 | INSERT/UPDATE em massa | Custo de manutenção do índice | Overhead |

Cada linha: capturar plano antes/depois, métricas, N execuções.

