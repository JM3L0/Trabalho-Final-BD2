# Cerebro — Trabalho Final de BD II (UFPI 2026.2)

Fonte da verdade: `Trabalho Final.pdf`. **[PDF]** = literal; **[DERIVADO]** = inferencia; **[DECISAO]** = a definir pelo grupo.

## Essencia
- Paper <= 10 pags, template SBC em LaTeX, sobre indices, plano de execucao e otimizacao de consultas (7,0).
- Experimentos no **Microsoft SQL Server Developer** (via Docker), com resultados no artigo ([justificativa](../comparativo-sgbds.md)).
- Apresentacao <= 20 min, demo bem-vinda (3,0).
- Submissao **17/11/2026**; apresentacao **18 e 19/11/2026**.

## Status Atual (13/11/2026)
- [x] Enunciado analisado e requisitos mapeados.
- [x] SGBD definido: **SQL Server 2022 Developer** em Docker ([ambiente.md](06-experimentacao/ambiente.md)).
- [x] Plano de implementacao completo elaborado, auditado e homologado ([plano-de-implementacao.md](../plano-de-implementacao.md)).
- [x] Dataset definido: E-Commerce B2C sintetico (~6,25M registros) com `seed=42` ([ambiente.md](06-experimentacao/ambiente.md)).
- [x] Arquitetura de testes definida: Duas bases na mesma instancia (`Ecommerce_Baseline` e `Ecommerce_Otimizado` via backup/restore).
- [x] Suporte multiplataforma homologado para Windows e Ubuntu (Docker Compose, Python/`uv`, `pathlib`, `pymssql`, `.gitattributes`).
- [x] Template SBC obtido no repositorio (`SBC_Conferences_Template___updated_sbc_template_sty_v2017__1_.zip`).
- [ ] Subir container do SQL Server (`docker compose up -d`).
- [ ] Executar script de geracao e carga dos dados sinteticos.
- [ ] Criar clone `Ecommerce_Otimizado` e aplicar indices secundarios.
- [ ] Executar bateria automatizada de testes estatisticos (N >= 30, MAXDOP controlado).

## Mapa
| Arquivo | Conteudo |
|---|---|
| [Plano de Implementacao](../plano-de-implementacao.md) | Roteiro completo do projeto em 6 fases |
| [00 texto-integral-pdf](00-visao-geral/texto-integral-pdf.md) | Transcricao fiel do enunciado |
| [01 requisitos](01-requisitos/requisitos.md) | Requisitos e pontuacao |
| [03 cronograma](03-prazos/cronograma.md) | Prazos e plano |
| [04 sugestoes](04-sugestoes-professor/sugestoes.md) | Sugestoes do professor |
| [05 teoria](05-referencial-teorico/teoria.md) | Referencial teorico e referencias |
| [06 ambiente](06-experimentacao/ambiente.md) | SGBD, infraestrutura multiplataforma e dataset |
| [06 metodologia](06-experimentacao/metodologia.md) | Protocolo experimental e analise estatistica |
| [06 plano de consultas](06-experimentacao/plano-de-consultas.md) | Catalogo detalhado de consultas (Q1–Q10 e W1) |
| [06 registro de resultados](06-experimentacao/registro-resultados.md) | Tabela e formato de registro dos resultados |
| [07 paper](07-paper-latex/paper.md) | Estrutura e template SBC (limite 10 pags) |
| [08 apresentacao](08-apresentacao/apresentacao.md) | Roteiro de 20 min e demo com duas bases |
| [09 decisoes e riscos](09-decisoes-e-pendencias/decisoes-e-riscos.md) | Decisoes consolidadas, pendencias e riscos mitigados |
| [10 checklist final](10-checklists/checklist-final.md) | Validacao antes de entregar |
