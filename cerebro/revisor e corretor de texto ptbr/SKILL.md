---
name: revisar-texto-ptbr
description: Varre um texto em português do Brasil atrás de TODOS os indícios de escrita gerada por IA (vocabulário e fórmulas genéricas, tom promocional, resíduos de chatbot, formatação mecânica, referências suspeitas) e já corrige cada um no texto, junto com ortografia, gramática e pontuação, mantendo a voz do autor. Use sempre que o usuário colar ou anexar um texto (trabalho acadêmico, TCC, artigo, relatório, e-mail, post, currículo, carta) e pedir para revisar, corrigir, melhorar, ajustar, deixar mais natural, "humanizar", tirar o tom de ChatGPT, achar ou remover sinais de IA, ou checar se parece escrito por IA, mesmo que não use a palavra "skill".
---

# Achar e corrigir os indícios de IA em texto em português do Brasil

O objetivo é pegar o texto do usuário, **achar todos os indícios de escrita de IA e corrigi-los no próprio texto**, devolvendo uma versão pronta para uso, **sem trocar a voz dele nem inventar conteúdo**. Quem assina o texto é o autor, então a revisão precisa ser fácil de conferir e fiel ao que ele quis dizer.

Dois arquivos de apoio, para ler quando for aplicar cada etapa:
- `references/correcao-ptbr.md`: checklist de ortografia, gramática e pontuação do português brasileiro.
- `references/sinais-ia-ptbr.md`: padrões de texto genérico ou "com cara de IA", adaptados ao português, com o que fazer em cada caso.

## Fluxo

1. **Leia o texto inteiro** antes de mexer. Se o usuário disse que anexou um arquivo, confira que ele existe. Identifique o gênero e o público (acadêmico, profissional, informal) pelo próprio texto; só pergunte se a resposta mudar muito a revisão.
2. **Varredura completa dos indícios de IA.** Leia `references/sinais-ia-ptbr.md` e percorra o texto **categoria por categoria** (conteúdo, linguagem, estilo e formatação, resíduos de conversa e de ferramenta, citações), anotando cada ocorrência com o trecho exato. Percorrer por categoria, e não só "de olho", é o que evita deixar passar sinais; vale também para o texto curto. Faça isso sempre, mesmo que o pedido seja só "revise" ou "corrija".
3. **Corrija cada ocorrência no texto.** Escolha a **menor** correção que resolve o problema de fundo:
   - frase ou oração que só enfeita ou repete (ressalva, resumo, gerúndio de "importância", abertura panorâmica): **corte**;
   - palavra ou fórmula de efeito (vocabulário recorrente, tom promocional, paralelismo negativo, regra de três): **troque pelo termo simples e específico** ou reescreva a frase de modo direto;
   - atribuição vaga ou afirmação sem apoio: mantenha só se o autor der a fonte; senão atenue como opinião própria ou marque `[CONFERIR]`;
   - resíduos (falas de chatbot, Markdown vazado, `utm_source`, lacunas): **remova**;
   - formatação mecânica (negrito, emojis, Title Case, listas em negrito, travessões em excesso): **normalize**.
4. **Correção gramatical.** Aplique o checklist de `references/correcao-ptbr.md`: ortografia pós-Acordo, acentuação, crase, concordância, regência, pontuação, confusões comuns, gerundismo e calcos do inglês.
5. **Segunda varredura no texto já corrigido.** Releia procurando sinais que sobraram ou que as próprias trocas criaram (trocar "crucial" por "fundamental" não resolve nada, e cortes podem deixar conectivos soltos). Repita até não restar nenhum. Depois confira: o sentido é o mesmo, não entrou nenhum fato novo, e números, nomes, siglas e citações estão idênticos ao original.
6. **Entregue** no formato abaixo.

Se o usuário pedir expressamente **só** correção gramatical, pule as etapas 2 e 3.

## Princípios

- **Corrija todos os indícios, e só eles.** Cada sinal encontrado deve ser tratado; o que não é sinal nem erro fica como está. Mantenha a voz, a ordem, os termos técnicos e o nível de formalidade. Uma reescrita total apaga a autoria e obriga o usuário a reler tudo.
- **Mesmo formato do original.** Texto simples volta como texto simples, sem negrito, listas ou títulos novos. Se o original é .docx, edite no próprio formato (use a skill de docx); se é LaTeX, preserve os comandos. Não reformate citações ABNT ou SBC: no máximo sinalize inconsistência.
- **Nunca invente.** Fatos, números, fontes, DOIs, nomes e datas só entram se o autor os forneceu. A cura real do texto genérico é a especificidade, e só o autor tem os dados. Por isso o caminho padrão é **cortar** a frase vazia; use `[ESPECIFICAR: o que entra aqui]` só quando a frase carrega uma afirmação importante que ficaria sem apoio, e liste nas pendências. Não encha o texto de marcadores.
- **Referências suspeitas** (autor, ano ou periódico que não batem, DOI que não resolve, afirmação "segundo estudos" sem fonte): não corrija nem apague; marque com `[CONFERIR]` e liste.
- **Respeite o registro.** O português acadêmico e formal tem fórmulas legítimas ("Nesse sentido", "Dessa forma", "Diante disso", conclusões ao fim). Só mexa quando forem repetitivas ou vazias.
- **Não trate como defeito** gramática correta, vocabulário culto, uma ou duas aspas curvas ou travessões, texto em tópicos em contexto técnico (README, slides) ou termo técnico que parece "palavra de IA" (ex.: "robusto" em engenharia).
- **Sem acusação.** Nunca diga que o texto "foi feito por IA"; fale em trecho genérico ou padrão de IA e no que foi corrigido. Se perguntarem se o texto "passa em detector", explique que detectores erram bastante e que nenhuma revisão garante resultado: o que a skill faz é eliminar os padrões e deixar o texto mais específico.

## Formato da entrega

1. **Texto corrigido**, completo, no formato do original.
2. **Indícios encontrados e corrigidos**: lista **completa**, uma linha por ocorrência (ou por grupo de ocorrências iguais), no formato `sinal: "trecho original" → o que virou (ou "cortado")`. Agrupe por categoria. Não resuma nem limite o número de itens: o usuário quer conferir que nada ficou de fora.
3. **Correções gramaticais**: resumo curto, com os exemplos mais relevantes.
4. **Pendências para você**: itens `[ESPECIFICAR]`, `[CONFERIR]` e qualquer afirmação sem fonte.

Seja direto. Se o texto não tinha indícios, diga isso e liste só o que de fato mudou.
