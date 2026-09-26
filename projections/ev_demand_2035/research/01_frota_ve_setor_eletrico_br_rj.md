# Pesquisa: frota de veículos elétricos e setor elétrico (Brasil e RJ)

> Relatório gerado por agente de pesquisa (WebSearch/WebFetch) em 2026-09-26.
> Mantido como fonte primária de rastreabilidade para os parâmetros usados no
> modelo de projeção 2035. Não editar os valores abaixo — qualquer correção
> deve ser feita via nova pesquisa e novo arquivo versionado, para preservar
> auditabilidade (mesmo princípio de imutabilidade da camada RAW do datalake).

## 1. Consumo atual de energia elétrica no Brasil — DADO OBSERVADO

Fonte primária: **EPE — Balanço Energético Nacional (BEN) 2025, Relatório Síntese, ano base 2024**, publicado 28/05/2025.
https://www.epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/PublicacoesArquivos/publicacao-885/topico-767/BEN_S%C3%ADntese_2025_PT.pdf

- **Consumo Final de Eletricidade (Brasil, 2024): 650,4 TWh** (+5,5% vs 2023: 616,3 TWh)
- Oferta Interna de Energia Elétrica (OIEE) 2024: 762,9 TWh (+5,5%)
- Geração total 2024: 751,3 TWh (+6,1% vs 2023)
- Consumo por classe (2024): Residencial 179,65 TWh aprox. (crescimento 8%), Industrial +9,3 TWh (+4,1%), Comercial +7,7 TWh (+7,4%)
- OIEE per capita 2024: 3.596 kWh/hab

Dado mais recente (mensal, não fechado no ano): consumo nacional em dez/2025 foi 47.616 GWh (+0,5% a/a) — Fonte: EPE, Resenha Mensal do Mercado de Energia Elétrica.

## 2. Geração de energia elétrica no Brasil — capacidade instalada por fonte — DADO OBSERVADO

Fonte primária: **EPE — BEN 2025, ano base 2024** (mesma fonte acima), capítulo "O uso da energia elétrica".

Capacidade instalada centralizada (GW), 2024:

| Fonte | 2023 | 2024 | Δ% |
|---|---|---|---|
| Hidrelétrica | 109,9 | 109,9 | 0,0% |
| Térmica (biomassa+gás+petróleo+carvão) | 47,5 | 46,4 | -2,3% |
| Nuclear | 2,0 | 2,0 | 0,0% |
| Eólica | 28,7 | 29,6 | +3,0% |
| Solar (centralizada) | 37,8 | 48,5 | +28,1% |
| **Total centralizado** | **226,0** | **236,4** | **+4,6%** |

Adicionalmente, Micro/Minigeração Distribuída (MMGD) solar: **35.892 MW** instalados em 2024 (+36% vs 2023).

Dado mais recente e "atual" (fonte secundária, imprensa a partir de dados ANEEL/SIGA, base setembro/2026):
- Capacidade centralizada total: **~220,7 GW** em 08/09/2026 (Hidráulica ≈46,6%, Térmica ≈22,8%, Solar ≈15,8%, Eólica ≈10,7%)
- Nota: esse número usa recorte diferente do BEN (só geração centralizada, sem contar toda MMGD do mesmo jeito) — trate como estimativa/proxy, não diretamente comparável linha a linha com a tabela acima.

Fontes: https://www.gov.br/aneel/pt-br/assuntos/noticias/2026/aneel-preve-crescimento-de-9-1-gw-na-matriz-eletrica-brasileira-em-2026 ; https://cenarioenergia.com.br/2026/09/14/brasil-adiciona-485-gw-a-matriz-eletrica-ate-agosto-aponta-aneel/

## 3. PDE 2034 — evolução prevista da matriz e consumo elétrico até 2034 — DADO OBSERVADO (fonte primária EPE)

Fonte primária lida diretamente: **EPE — PDE 2034, Caderno "Demanda de Eletricidade"**, agosto/2024.
https://www.epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/PublicacoesArquivos/publicacao-804/topico-709/PDE%202034_Caderno_Demanda_Eletricidade_Publicacao.pdf

Cenário de referência 2024→2034:

- **Consumo total de eletricidade (Brasil): de ~538 TWh (2014) a 870 TWh em 2034**, crescimento médio de **3,4% a.a.** (cenário superior: 930 TWh/4,0% a.a.; inferior: 807 TWh/2,7% a.a.)
- Consumo residencial: +3,0% a.a., chegando a 226 TWh em 2034, com 91 milhões de consumidores e 202 kWh/mês médio
- Consumo industrial: +3,0% a.a. (cenário referência), chegando a 262 TWh em 2034
- Consumo comercial: +4,4% a.a., 157 TWh em 2034
- Consumo total de todas as classes (rede): 774 TWh em 2034 (residencial 29%, industrial 34%, comercial 20%, outras 17%)
- Autoprodução não injetada na rede: crescimento 2,4% a.a., 91,8 TWh em 2034
- Carga de energia (SIN, GWmédio): de 67 GWmédio (2018) a **107 GWmédio em 2034**, crescimento médio 3,3% a.a. (superior: 116 GWmédio; inferior: 100 GWmédio), com aceleração maior na segunda metade da década (4,1 GWmédio/ano de acréscimo em 2029-2034 vs 2,8 em 2024-2029)
- Elasticidade-renda do consumo: 1,20 (cenário referência); PIB 2,8% a.a. → consumo 3,4% a.a.

Expansão de capacidade por fonte até 2034 (fonte secundária — reportagens especializadas citando o PDE 2034 aprovado em abril/2025; não confirmado por leitura direta do caderno de oferta, portanto classificar como **estimativa/derivada de fonte secundária confiável**):
- Geração total: de 759 TWh (2024) para 1.045 TWh (2034)
- Hidráulica: modernização de usinas ~6,3-6,4 GW + 3,2 GW de PCH/CGH novas
- Eólica: +15,5 GW até 2034
- Térmica a gás natural: +28,1 GW (dos quais 3,8 GW de novos contratos de usinas já em operação)
- Biomassa: +2,27 GW
- Renovabilidade da matriz elétrica (2034): **86,1%**

Fontes: https://www.alemdaenergia.engie.com.br/pde-2034-mostra-renovaveis-e-gas-natural-em-crescimento/ ; https://cenarioenergia.com.br/2025/04/09/pde-2034-brasil-aposta-em-renovaveis-e-gas-natural-para-liderar-a-transicao-energetica/ ; PDE 2034 aprovado abril/2025: https://www.epe.gov.br/pt/imprensa/noticias/mme-aprova-plano-decenal-de-expansao-de-energia-2034-em-portaria

Observação importante para calibração do modelo: já existe um **PDE 2035** mais novo (o Caderno de Premissas Demográficas e Econômicas do PDE 2035 já é citado como referência em documentos EPE de 2025/2026), mas não foi localizado diretamente o Caderno de Demanda de Eletricidade do PDE 2035 nesta pesquisa — verificar em https://www.epe.gov.br/pt/publicacoes-dados-abertos/publicacoes/plano-decenal-de-expansao-de-energia-2034 (ou 2035) se já publicado, pois substituirá parcialmente os números acima.

## 4. Frota atual de veículos elétricos leves no Brasil — DADO OBSERVADO

Fonte primária mais robusta: **EPE — Nota Técnica "Demanda de Energia dos Veículos Leves: 2026-2035"**, EPE/DPG/SDB/2026/01, publicada 09/03/2026 (lida integralmente).
https://www.epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/PublicacoesArquivos/publicacao-331/topico-827/NT-EPE-DPG-SDB-2026-01_Demanda%20de%20energia%20VL_2026-2035.pdf

- Vendas de eletrificados (BEV+PHEV+HEV) em 2025: **~224 mil unidades**, 9% do total de licenciamentos de veículos leves (2,549 milhões em 2025), crescimento de 26% vs 2024 (177 mil unidades, 7,1% do total)
- Divisão 2025: PHEV 4% das vendas totais de leves, BEV 3,1%, HEV 1,7%
- Frota circulante de BEV+PHEV (EPE, citando OLADE 2025): estimada em **~395 mil veículos em 2024**
- Fonte adicional (ABVE, dado mais recente que o corte do documento EPE): **frota acumulada nacional de veículos eletrificados (BEV+PHEV+HEV+HEV Flex) atingiu 1 milhão de unidades em 24/09/2026** — atenção: este número da ABVE é "emplacamentos acumulados" desde 2012, conceito mais amplo (inclui HEV convencional) e não idêntico ao "frota circulante BEV+PHEV" citado pela EPE/OLADE. Em agosto/2026 o acumulado ABVE era 950.183 unidades.

Fontes: https://abve.org.br/frota-eletrificada-chega-a-um-milhao-de-veiculos-no-brasil-a-eletromobilidade-ja-e-o-presente/ ; https://www.otempo.com.br/autotempo/2026/9/24/frota-eletrificada-no-brasil-atinge-1-milhao-de-carros-veja-os-numeros-em-detalhe

## 5. Estimativas de crescimento da frota de VEs no Brasil até 2030/2035 — ESTIMATIVA/PROJEÇÃO

**A) EPE (Nota Técnica 2026-2035, cenário de referência — fonte primária, mais robusta):**
- Licenciamento de leves total: crescimento médio 4,5% a.a. (2026-2035), chegando a ~4 milhões de veículos novos/ano em 2035
- Participação de eletrificados no licenciamento: **8% em 2026 → ~10-11% em 2030 → 23% em 2035** (HEV 3%→4%→6%; PHEV 2%→3%→3%; BEV 3%→4%→13%, aproximadamente, conforme Gráfico 9 do documento)
- Participação de eletrificados na frota circulante total: ~2% (2026) → 4-5% (2030) → 8% (2035)
- **Demanda de eletricidade para recarga de BEV+PHEV: 0,7 TWh (2026) → 1,8 TWh (2030) → 3,4 TWh (2035)** — cenário de referência. Provavelmente o dado mais diretamente utilizável para o modelo de demanda elétrica.
- Nota: uma edição anterior desta série (Nota Técnica 2025-2034, dez/2024) mencionava um "cenário turbo eletrificação" com eletrificados atingindo 22% da frota e demanda de recarga de 5,0 TWh em 2034 — indica que a EPE também trabalha com cenário mais agressivo além do de referência (texto completo não lido nesta pesquisa).

**B) ABVE (declarações do presidente Ricardo Bastos, cenário do setor):**
- Projeção para 2030: 30% dos emplacamentos totais serão eletrificados (excluindo micro-híbridos), sendo metade PHEV, 7,5% HEV convencional e 7,5% BEV.
Fonte: https://www.autodata.com.br/noticias/2024/05/13/abeifa-e-abve-calculam-que-eletricos-representarao-7-5-do-mercado-em-2030/72096/

**C) Consultoria Bright (citada por ClimaInfo/IHU, jul/2024) — projeção de frota, não vendas:**
- Frota de carros 100% elétricos (BEV) em circulação: de 39,1 mil (fim de 2023) para **1,4 milhão em 2030** (2,35% da frota total projetada de leves, 57 milhões em 2030).
Fonte: https://climainfo.org.br/2024/07/23/brasil-tera-14-milhao-de-carros-eletricos-em-circulacao-em-2030-projeta-consultoria/ (não confirmado por leitura direta).

**D) IEA — Global EV Outlook 2025 (contexto internacional, Brasil citado):**
- Vendas de VEs no Brasil em 2024: mais que dobraram para ~125 mil (6% de market share) — difere do ABVE (177 mil incluindo HEV); diferença de escopo (IEA conta só BEV+PHEV).
- Q1/2025: vendas de VEs no Brasil passaram de 30 mil (+40% vs Q1/2024)
- No Brasil, BEV representa minoria (45%) das vendas de elétricos "puros", maioria é PHEV.
Fonte: https://www.iea.org/reports/global-ev-outlook-2025

**E) BloombergNEF — NÃO ENCONTRADO** número específico e verificável de participação de mercado do Brasil para 2030 (PDF do roadmap Brasil/CIF-BNEF bloqueado para acesso). Dado solto não verificado: "vendas de VE no Brasil devem quintuplicar até 2027" (BNEF Long-Term EV Outlook, citado em fonte secundária sem número exato).

## 6. Consumo atual de energia elétrica no Rio de Janeiro (estado) — NÃO ENCONTRADO (número absoluto exato)

Não obtido número absoluto e citável de consumo total anual de eletricidade do estado do RJ em TWh/GWh nesta pesquisa (dashboard EPE não pôde ser lido programaticamente).

Indícios parciais (não verificados por leitura direta, tratar como pistas):
- RJ teve queda de -3,4% no consumo residencial em 2025 (a/a)
- RJ teve alta de +8,3% no consumo comercial em fevereiro/2025 (a/a)

**Já temos dados próprios da EPE/ONS para o RJ (datalake deste repositório) — usar isso como fonte primária; usar os itens acima só como checagem cruzada.**

## 7. Frota de veículos elétricos no Rio de Janeiro (estado) — DADO OBSERVADO (fonte de imprensa citando Detran-RJ e ABVE)

- Detran-RJ (Anuário do Trânsito): frota de carros elétricos no estado do RJ passou de **3.263 veículos em 2021 para mais de 30.000 em 2025** (+839% em 4 anos).
  Fonte: https://www.band.com.br/bandnews-fm/rio-de-janeiro/noticias/numero-de-carros-eletricos-no-rio-cresce-839-em-quatro-anos-202607291346 (jul/2026; WebFetch bloqueado para este domínio, via resumo de busca)
- Ranking nacional por estado (jan/2026, fonte de imprensa citando registros ABVE/Detran por UF): **RJ é o 3º estado em veículos eletrificados, com 39.295 unidades**, atrás de SP (líder) e DF (2º, 48.502), à frente de MG (37.897) e PR (37.703).
- Emplacamento de elétricos/híbridos no RJ cresceu **82% entre janeiro e julho de 2026** (a/a). Fonte: https://www.brasilemfolhas.com.br/2026/09/vendas-de-carros-eletricos-crescem-82-no-rio-de-janeiro/ (via resumo de busca)
- Os elétricos ainda representam apenas **0,35% da frota total de veículos do RJ** (frota total ~8,7 milhões de veículos).
- Dado municipal complementar (EPE, Nota Técnica VL 2026-2035, fonte primária): entre 2022-2025, o **município do Rio de Janeiro** vendeu 14.568 unidades de BEV+PHEV (4º colocado entre municípios brasileiros, atrás de São Paulo 46.274, Brasília 36.476, Belo Horizonte 14.874). No município do RJ há **1 eletroposto (ponto de recarga) para cada 15 VEs**, uma das melhores relações do país (São Paulo: 1 para 22; Brasília: 1 para 58).

Nota de rastreabilidade: itens de imprensa (band.com.br, brasilemfolhas.com.br, "39.295 unidades") tiveram WebFetch bloqueado pelo proxy de rede deste ambiente — números vêm de resumos do WebSearch, não de leitura integral da página. Recomenda-se confirmação manual antes de uso em publicação formal, embora sejam consistentes entre si e com a ordem de grandeza esperada.

## 8. Projeção de crescimento da frota elétrica especificamente para o Rio de Janeiro — NÃO ENCONTRADO

Não existe, no material localizado, projeção quantitativa (2030/2035) de frota de VEs específica para o estado do RJ, publicada por EPE, ABVE, Detran-RJ ou consultorias. Nenhum documento nacional (PDE 2034/2035, Nota Técnica de Veículos Leves) desagrega a projeção por UF.

**Recomendação explícita do pesquisador**: derivar a projeção do RJ proporcionalmente à frota/projeção nacional, usando como "peso" a participação atual do RJ na frota nacional. Bases de proporção disponíveis:
- RJ ~39.295 unidades (jan/2026) vs frota nacional ~1.000.000 (set/2026, conceito mais amplo incluindo HEV) → participação bruta ~3,9% (cuidado: escopos não diretamente comparáveis, ajuste necessário).
- Alternativa mais consistente: usar a base municipal EPE 2022-2025 (Rio de Janeiro-capital = 14.568 BEV+PHEV vendidos, ~4º lugar nacional) como proxy de peso regional, por ser fonte primária EPE com metodologia comparável ao resto da Nota Técnica usada no item 5.

---

## TABELA-RESUMO CONSOLIDADA

| # | Item | Valor | Unidade | Ano ref. | Classificação | Fonte |
|---|---|---|---|---|---|---|
| 1 | Consumo final de eletricidade, Brasil | 650,4 | TWh | 2024 | Observado | EPE, BEN 2025 |
| 2a | Capacidade instalada hidrelétrica | 109,9 | GW | 2024 | Observado | EPE, BEN 2025 |
| 2b | Capacidade instalada eólica | 29,6 | GW | 2024 | Observado | EPE, BEN 2025 |
| 2c | Capacidade instalada solar (centralizada) | 48,5 | GW | 2024 | Observado | EPE, BEN 2025 |
| 2d | Capacidade instalada térmica | 46,4 | GW | 2024 | Observado | EPE, BEN 2025 |
| 2e | Capacidade instalada nuclear | 2,0 | GW | 2024 | Observado | EPE, BEN 2025 |
| 2f | MMGD solar | 35,9 | GW | 2024 | Observado | EPE, BEN 2025 |
| 2g | Capacidade centralizada total (mais recente) | ~220,7 | GW | set/2026 | Observado (proxy, recorte diferente) | ANEEL/imprensa |
| 3a | Crescimento médio anual do consumo elétrico | 3,4 | %a.a. | 2024-2034 | Observado (PDE 2034, cenário referência) | EPE, PDE 2034 |
| 3b | Consumo total de eletricidade projetado | 870 | TWh | 2034 | Observado (projeção primária EPE) | EPE, PDE 2034 |
| 3c | Carga de energia (SIN) projetada | 107 | GWmédio | 2034 | Observado (projeção primária EPE) | EPE, PDE 2034 |
| 3d | Expansão eólica prevista | +15,5 | GW | até 2034 | Estimativa (fonte secundária sobre PDE 2034) | Imprensa especializada |
| 3e | Expansão térmica a gás | +28,1 | GW | até 2034 | Estimativa (fonte secundária sobre PDE 2034) | Imprensa especializada |
| 3f | Renovabilidade da matriz elétrica projetada | 86,1 | % | 2034 | Estimativa (fonte secundária sobre PDE 2034) | Imprensa especializada |
| 4a | Vendas de eletrificados (BEV+PHEV+HEV) | 224 mil (9% do total) | unidades | 2025 | Observado | EPE (NT VL 2026-2035) / ABVE |
| 4b | Frota circulante BEV+PHEV | ~395 mil | unidades | 2024 | Observado (estimativa oficial EPE/OLADE) | EPE (NT VL 2026-2035) |
| 4c | Frota acumulada nacional eletrificados (conceito amplo) | 1.000.000 | unidades | 24/09/2026 | Observado | ABVE |
| 5a | Participação eletrificados no licenciamento | 23 | % | 2035 | Projeção primária EPE (cenário referência) | EPE (NT VL 2026-2035) |
| 5b | Demanda de eletricidade p/ recarga BEV+PHEV | 3,4 | TWh | 2035 | Projeção primária EPE (cenário referência) | EPE (NT VL 2026-2035) |
| 5c | Demanda de eletricidade p/ recarga BEV+PHEV | 1,8 | TWh | 2030 | Projeção primária EPE (cenário referência) | EPE (NT VL 2026-2035) |
| 5d | Frota BEV projetada (consultoria Bright) | 1,4 milhão | unidades | 2030 | Projeção de terceiros (não verificada por leitura direta) | Bright/ClimaInfo |
| 5e | Participação BNEF/2030 Brasil | — | — | — | Não encontrado | — |
| 6 | Consumo elétrico total do estado do RJ | — | TWh | — | Não encontrado (nesta pesquisa) | — |
| 7a | Frota de VEs no estado do RJ | >30.000 | unidades | 2025 | Observado | Detran-RJ (via imprensa) |
| 7b | Frota de VEs no estado do RJ (ranking nacional) | 39.295 (3º lugar) | unidades | jan/2026 | Observado | Imprensa (fonte não lida integralmente) |
| 7c | Crescimento emplacamento VE/híbrido no RJ | +82 | % | jan-jul/2026 vs 2025 | Observado | Imprensa (fonte não lida integralmente) |
| 7d | Vendas BEV+PHEV no município do RJ | 14.568 | unidades acumuladas | 2022-2025 | Observado (fonte primária EPE) | EPE (NT VL 2026-2035) |
| 8 | Projeção de frota de VEs específica para RJ | — | — | — | Não encontrado — derivar proporcionalmente | — |

## Observações finais sobre qualidade das fontes

1. **Melhor achado desta pesquisa**: a Nota Técnica EPE "Demanda de Energia dos Veículos Leves: 2026-2035" (publicada 09/03/2026, lida na íntegra) é a fonte mais valiosa para o modelo, pois entrega diretamente a demanda de eletricidade projetada para recarga de VEs leves no Brasil (0,7 / 1,8 / 3,4 TWh em 2026/2030/2035, cenário de referência), com metodologia detalhada e ligação direta ao PDE 2035.
2. Vários domínios (gov.br, abve.org.br, cenarioenergia.com.br, engie, otempo.com.br, brasilemfolhas.com.br, evdrops.com.br, climainfo.org.br, cif.org) estavam bloqueados para WebFetch neste ambiente (proxy de rede) — dados desses domínios vêm de resumos do WebSearch, não de leitura integral da página.
3. Divergência de escopo importante para calibração: "eletrificados" (ABVE/EPE, inclui HEV convencional) ≠ "elétricos plugáveis" BEV+PHEV (IEA/EPE em outras seções) ≠ "100% elétricos" BEV isolado (Bright/consultoria). Os números de frota variam bastante conforme o escopo (ex.: 1 milhão vs 395 mil vs 224 mil/ano) — o modelo fixa explicitamente o escopo BEV+PHEV (mais relevante para demanda de recarga elétrica).
4. Já existe um ciclo de planejamento mais novo, o **PDE 2035**, cujo Caderno de Premissas Demográficas e Econômicas já está em uso pela EPE (citado como referência na Nota Técnica de Veículos Leves de março/2026), mas cujo Caderno de Demanda de Eletricidade não foi localizado/confirmado publicado nesta pesquisa — vale conferir se já saiu, pois substituiria os números do PDE 2034 usados no item 3.
