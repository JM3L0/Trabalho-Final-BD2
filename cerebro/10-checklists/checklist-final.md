# Checklist Final de Conformidade

## 1. Setup, Infraestrutura e Dados
- [x] SGBD comercial (nao MySQL) definido: **Microsoft SQL Server 2022 Developer**
- [x] Plano de implementacao completo elaborado e aprovado por subagentes ([plano-de-implementacao.md](../../plano-de-implementacao.md))
- [x] Dataset definido: E-Commerce B2C sintetico com ~6,25 milhoes de registros (`seed=42`)
- [x] Estrategia de bases gemeas definida: `Ecommerce_Baseline` e `Ecommerce_Otimizado` via backup/restore nativo
- [x] Compatibilidade multiplataforma (Windows e Ubuntu) assegurada no planejamento
- [ ] Container Docker em execucao (`docker compose up -d`)
- [ ] Permissoes do diretorio `./data` ajustadas no Linux (`chmod -R 777 ./data`)
- [ ] Smoke test de captura de `SET STATISTICS IO, TIME ON` via `pymssql` validado
- [ ] Dados gerados (vetorizacao `numpy`, `seed=42`) e carregados na base baseline via `BULK INSERT` (com `RECOVERY SIMPLE`)
- [ ] Clone `Ecommerce_Otimizado` restaurado com sucesso (e CSVs temporarios limpos se necessario)
- [ ] Indices secundarios criados na base otimizada
- [ ] Planos reais (`SET STATISTICS XML ON`) de Q1 a Q10 e W1 validados antes do loop estatistico
- [ ] Metricas e versoes exatas registradas (`SELECT @@VERSION;` e `sp_spaceused`)
- [ ] Benchmark automatizado de Q1 a Q10 e W1 executado ($N \ge 30$ em Warm Cache + Cold Cache calibrado, `MAXDOP 1`)

## 2. Artigo Cientifico (Paper em LaTeX)
- [ ] Pacote oficial SBC descompactado (`SBC_Conferences_Template___updated_sbc_template_sty_v2017__1_.zip`) e esqueleto LaTeX criado
- [ ] Limite estrito de no maximo 10 paginas respeitado no PDF final
- [ ] Formatacao original da SBC preservada sem alteracao de margens ou fontes
- [ ] Cobertura dos tres temas obrigatorios: indices, plano de execucao e otimizacao
- [ ] Fundamentacao teorica consistente com citacoes no padrao SBC (`sbc.bst`)
- [ ] Metodologia experimental detalhada (hardware, SGBD, dataset, MAXDOP, protocolo)
- [ ] Tabela comparativa unificada contendo Leituras Logicas, Tempos, Speedup e testes estatisticos
- [ ] Diagramacao grafica de no maximo 3 a 4 figuras de planos de execucao representativos
- [ ] Analise do trade-off de escrita (operacao W1)
- [ ] Compilacao multiplataforma validada sem advertencias graves
- [ ] Revisao textual e ortografica completa
- [ ] Submissao realizada ate **17/11/2026**

## 3. Apresentacao Oral e Demonstracao Pratica
- [ ] Slides elaborados e ajustados para o tempo alvo de 17 a 18 minutos
- [ ] Kit de demonstracao pratica configurado com duas abas lado a lado (`Ecommerce_Baseline` vs `Ecommerce_Otimizado`)
- [ ] Scripts de demonstracao numerados e testados
- [ ] Gravacao prévia de video de contingencia como backup operacional
- [ ] Confirmacao do dia exato de apresentacao (18 ou 19/11/2026)
