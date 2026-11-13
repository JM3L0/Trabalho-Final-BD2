# Checklist Final de Conformidade

## 1. Setup, Infraestrutura e Dados
- [x] SGBD comercial (nao MySQL) definido: **Microsoft SQL Server 2022 Developer**
- [x] Plano de implementacao completo elaborado e aprovado por subagentes ([plano-de-implementacao.md](../../plano-de-implementacao.md))
- [x] Dataset definido: E-Commerce B2C sintetico com ~6,25 milhoes de registros (`seed=42`)
- [x] Estrategia de bases gemeas definida: `Ecommerce_Baseline` e `Ecommerce_Otimizado` via backup/restore nativo
- [x] Compatibilidade multiplataforma (Windows e Ubuntu) assegurada no planejamento
- [ ] Container Docker em execucao (`docker compose up -d`)
- [ ] Permissoes do diretorio `./data` ajustadas no Linux (`chmod -R 775 ./data`)
- [ ] Dados gerados e carregados na base baseline via `BULK INSERT` (com `RECOVERY SIMPLE`)
- [ ] Clone `Ecommerce_Otimizado` restaurado com sucesso
- [ ] Indices secundarios criados na base otimizada
- [ ] Metricas e versoes exatas registradas (`SELECT @@VERSION;` e `sp_spaceused`)
- [ ] Benchmark automatizado de Q1 a Q10 e W1 executado ($N \ge 30$, `MAXDOP 1`)

## 2. Artigo Cientifico (Paper em LaTeX)
- [x] Pacote oficial SBC descompactado na raiz do projeto
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
