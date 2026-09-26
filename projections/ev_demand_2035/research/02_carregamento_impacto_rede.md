# Pesquisa: comportamento de carregamento de VEs e impacto na rede

> Relatório gerado por agente de pesquisa (WebSearch/WebFetch) em 2026-09-26.
> Várias fontes primárias (ANEEL/gov.br, ScienceDirect, DTU/orbit, EPRI,
> periodicorease.pro.br) estavam bloqueadas pelo proxy de rede deste
> ambiente; nesses casos os números vêm de resumos de busca, não de leitura
> integral — sinalizado item a item. Números marcados "estimativa derivada"
> foram calculados neste relatório, não citados diretamente por uma fonte.

## 1. Consumo médio de energia por VE leve (BEV)

**Dado brasileiro (INMETRO/PBEV):**
- PBEV (INMETRO) reporta consumo em MJ/km. BYD Dolphin Mini e Geely EX2 lideram com **0,39 MJ/km ≈ 10,8 kWh/100km** (bateria 38 kWh, autonomia homologada 280 km).
  Fonte: https://www.gov.br/inmetro/pt-br/centrais-de-conteudo/noticias/inmetro-atualiza-ranking-de-eficiencia-energetica-de-veiculos-e-amplia-base-no-brasil ; tabela completa: https://www.gov.br/inmetro/pt-br/assuntos/regulamentacao/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/veiculos-automotivos-pbe-veicular
- BYD Dolphin GS: bateria 44,9 kWh, autonomia PBEV 291 km → **estimativa derivada ≈15,4 kWh/100km**.
  Fonte dos dados brutos: https://www.mercadolivre.com.br/blog/mo-consumo-byd-dolphin-2026-consumo-autonomia-e-desempenho-por-versao
- Cross-check internacional (BYD Dolphin Europa): 15,9 kWh/100km combinado / 12,1 urbano. Fonte: https://www.byd.com/es-es/coches-electricos/dolphin (referência internacional).

**Referência internacional (EPA/DOE):**
- Chevrolet Bolt EUV (MY2022): ≈17,4-17,5 kWh/100km. Fonte: https://www.fueleconomy.gov/feg/Find.do?action=sbs&id=43954
- Faixa geral EPA BEVs MY2024: ordem de grandeza 15,5-25 kWh/100km. Fonte: https://www.energy.gov/cmei/vehicles/articles/fotw-1374-december-23-2024-model-year-2024-electric-vehicles-offer-consumers

**Quilometragem média anual (Brasil):** 10.000-15.000 km/ano (faixa de mercado citada 10.000-20.000).
Fontes: https://www.gazetadopovo.com.br/automoveis/km-rodado-ano-carro-motorista-brasil/ ; https://autopapo.com.br/noticia/quilometragem-media-carro-usado/ ; https://somob.com.br/2025/05/14/saiba-quantos-quilometros-um-veiculo-costuma-percorrer-por-ano-no-brasil/

**Estimativa derivada — consumo anual por veículo:** combinando 11-18 kWh/100km (central ~15) com 10.000-15.000 km/ano → **faixa 1.300-2.700 kWh/veículo/ano, valor central sugerido ~1.800-2.200 kWh/veículo/ano**. Estimativa derivada, não publicada diretamente por nenhuma fonte.

## 2. Características de carregamento residencial e público

| Tipo | Potência típica | Fonte |
|---|---|---|
| Tomada comum 110V/220V | ~1,4-2,3 kW (10-20A) | Referência técnica geral / IEA GEVO 2024 (internacional) |
| Wallbox monofásico dedicado | 7,4 kW (32A/220V) | WEG WEMOB (fabricante nacional): https://static.weg.net/medias/downloadcenter/h1c/h57/WEG-estacoes-de-recarga-de-veiculos-eletricos-WEMOB-50105757-pt.pdf |
| Wallbox trifásico | 11-22 kW | IEA GEVO 2024: https://www.iea.org/reports/global-ev-outlook-2024/outlook-for-electric-vehicle-charging-infrastructure |
| DC rápido público | 50-150 kW | WEG WEMOB (mercado BR) |
| DC ultrarrápido | >150 kW até 350 kW | Tesla Supercharger/BYD BR; IEA GEVO 2024 (internacional) |

**Norma brasileira ABNT NBR 17019:2022**: circuito exclusivo do carregador, **fator de utilização = 1 (100%)** no dimensionamento (carga contínua na potência máxima considerada no dimensionamento de cabos/disjuntores).
Fontes: https://canalsolar.com.br/abnt-publica-norma-para-instalacao-de-carregadores-de-veiculos-eletricos/ ; https://raceletrica.eng.br/blog/guia-nbr-17019-instalacao-carregadores-wallbox/

## 3. Horários típicos de recarga residencial e sobreposição com o pico do sistema

**Não foi encontrado estudo público brasileiro (COPPE/UFRJ, Light, Enel, CPFL) com dados empíricos de horário de conexão residencial de VEs.** Usar proxy internacional:

- Carregamento não controlado: pico de conexão residencial tipicamente **entre 17h30-18h30**, coincidindo com o pico vespertino/noturno de carga residencial de base. Gestão de carga pode deslocar para 22h-23h.
  Fonte: NREL 2021, https://docs.nrel.gov/docs/fy21osti/79080.pdf (internacional)
- NREL: "residentes concentram consumo elétrico entre 18h-20h, mesmo período em que tendem a conectar o VE ao chegar em casa" (internacional).

**Evidência indireta brasileira (desenho tarifário, não estudo comportamental):** horário de ponta Light-RJ é **17h30-20h30** (ponta), 20h30-22h30 (intermediário), 22h30-17h30 (fora de ponta) em dias úteis — ou seja, o horário de chegada típica do trabalho **coincide exatamente com o horário de ponta do sistema no RJ**.
Fonte: https://calculadoraenergia.com.br/tarifa/light (agregador, recomenda-se confirmar com Light/ANEEL diretamente).

**Recomendação do pesquisador**: usar o padrão internacional (pico de conexão ~17h30-19h, decaindo à noite) como proxy — razoável dado que o padrão de deslocamento casa-trabalho é estruturalmente semelhante.

## 4. Impacto da frota de VEs sobre demanda máxima e curva de carga

- Muratori (NREL), *Nature Energy* 2018: penetração de VE até **3% da frota** não impacta significativamente a demanda agregada residencial; mas **efeitos de concentração local ("clustering")** podem gerar picos locais significativos mesmo com baixa adoção agregada. Fonte: https://www.nature.com/articles/s41560-017-0074-z (internacional)
- NREL 2021: sistemas de distribuição podem sofrer **aumento de até 20% no pico de demanda** quando a maioria dos carregamentos inicia logo após o fim do horário de ponta (agendamento automático simultâneo). Fonte: https://docs.nrel.gov/docs/fy21osti/79080.pdf (internacional)
- Estudos brasileiros (CBA/SBA, REASE) sugerem que **para penetrações acima de 50% de VEs, ~30% dos alimentadores de distribuição precisariam de reforço estrutural** — **NÃO VERIFICADO em texto integral** (acesso bloqueado); usar com cautela, confiabilidade baixa/média.
  Fontes (título, não confirmado): https://www.sba.org.br/open_journal_systems/index.php/cba/article/view/1644 ; https://periodicorease.pro.br/rease/article/download/23003/14366/67615

## 5. Fator de simultaneidade / coincidence factor

- Ramadan et al. (DTU), IEEE Trans. Transportation Electrification 2021: **fator de coincidência cai para menos de 25% com mais de 50 VEs carregando a 11 kW**; diminui com mais VEs (diversificação estatística), aumenta com potências menores e temperaturas mais baixas. Fonte: https://orbit.dtu.dk/en/publications/coincidence-factors-for-domestic-ev-charging-from-driving-and-plu/ (internacional)
- Estudo 2025 (comunidades residenciais): fator de coincidência máximo **~23% às 18h**, caindo a **~1% às 6h**. Fonte: https://www.sciencedirect.com/science/article/pii/S2352484725008546 (internacional, texto bloqueado, via resumo)

**Uso sugerido**: fator de coincidência no pico entre **15% e 25%** da frota conectada carregando simultaneamente em potência plena (carregamento residencial não controlado, >50 veículos).

## 6. Impacto em transformadores e subestações de distribuição

- EPRI (via TD World, ScienceDirect): **~80% da recarga ocorre em casa**; VEs podem **dobrar ou triplicar a carga residencial** em um ponto de conexão; sobrecarga/envelhecimento acelerado de transformadores é um problema crítico. Fontes: https://www.tdworld.com/electrification/article/21278952/right-sizing-residential-transformers-for-evs ; https://doi.org/10.3390/en15239023 (internacional)
- Transformadores monofásicos residenciais tipicamente **10-50 kVA**; exemplo: transformador de 375 kVA com 200 kVA de carga de VEs atinge **>90% de carregamento**. Fonte: https://wppienergy.org/wp-content/uploads/resources/WPPI-2024-EV-Distribution-Guidebook_Final.pdf (internacional)
- Estratégias de carregamento residencial permitem cada uma até **~20% de penetração de VE** por comunidade antes de exigir intervenção; recomenda-se atualizar dimensionamento para suportar até 100%. Fonte: ScienceDirect 2025 (acima, internacional)
- Brasil: projetos de P&D ANEEL em mobilidade elétrica (Light — Chamada 22/2018; CPFL — Laboratório de Mobilidade Elétrica de Indaiatuba, R$17mi) existem, mas **sem quantificação pública de "VEs por transformador antes de reforço"** encontrada.
  Fontes: https://gesel.ie.ufrj.br/pesquisas/mobilidade-eletrica-compartilhada-light/ ; https://www.premioeco.com.br/projeto/projetos-de-pd-com-foco-em-mobilidade-eletrica/

## 7. Estratégias de carregamento: comparação de impactos

| Estratégia | Efeito no pico | Fonte |
|---|---|---|
| Não controlado ("dumb charging") | Aumento de até **20%** (agendamento simultâneo pós-ponta) | NREL 2021 (internacional) |
| TOU com início aleatorizado na janela fora-ponta | Redução de **~5%** | NREL 2021 (internacional) |
| Smart charging / V1G | Redução de **6%** (regional, norte da França 2040) a **66-74%** na potência de pico necessária (escala pan-europeia: 281-284 GW → 73-94 GW) | Estudos europeus V1G 2024-2026: https://arxiv.org/pdf/2602.01862 (internacional) |
| Deslocamento para PV solar diurno (workplace charging) | Cobertura de até **38%** da recarga por solar; redução de pico de até **45%** (Noruega, gestão compartilhada em edifícios) | ScienceDirect 2023/2024 (internacional) |

Nota: um número de "experimento McKinsey" (+30%→+16% com carregamento noturno) circulou nas buscas mas **não foi possível confirmar a publicação primária** — não incluído como confiável.

## 8. Tarifas e programas brasileiros

- **Tarifa Branca (ANEEL, REN 733/2016)**, em vigor desde 2018: 3 postos tarifários (ponta = 3h consecutivas em dias úteis; intermediário = 1h-1h30 antes/depois; fora de ponta = resto), definidos por distribuidora. Disponível a consumidores do Grupo B desde jan/2020, sem custo de adesão.
  Fontes: https://www.gov.br/aneel/pt-br/assuntos/tarifas/tarifa-branca ; https://www.gov.br/aneel/pt-br/assuntos/tarifas/entenda-a-tarifa/postos-tarifarios (BR oficial)
- **Light (RJ)** (fonte agregadora, confirmar com Light/ANEEL): ponta 17h30-20h30, intermediário 20h30-22h30, fora de ponta 22h30-17h30 (dias úteis). Exemplo de tarifas: ponta R$1,147/kWh, intermediário R$0,764/kWh, fora de ponta R$0,552/kWh, convencional R$0,626/kWh.
  Fonte: https://calculadoraenergia.com.br/tarifa/light (2026)
- **Copel (PR) — Tarifa Mobiflex**: piloto ANEEL, desconto para recarga domiciliar de VE entre **0h-6h**, economia de até **12%** na conta. Requer VE plug-in + wallbox.
  Fontes: https://www.parana.pr.gov.br/aen/Noticia/Copel-lanca-projeto-que-da-desconto-para-recarga-de-veiculos-eletricos-na-madrugada ; https://canalve.com.br/parana-desconto-recarga-carros-eletricos-madrugada/ (2025, BR)
- Recarregar de madrugada (23h-8h, tarifa branca) pode custar até **76% menos por km** que gasolina. Fonte: https://brasil.perfil.com/carros/carregar-o-carro-eletrico-de-madrugada-pode-custar-76-menos-que-abastecer-com-gasolina.phtml (2026, BR)
- Não encontrada tarifa de recarga específica de Enel ou CPFL (apenas programas gerais de frota corporativa).

## 9. Necessidade de expansão de geração/transmissão/distribuição — ACHADO PRINCIPAL

**EPE — PDE 2035, Caderno de Demanda de Eletricidade (publicado 2025)**:
https://www.epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/PublicacoesArquivos/publicacao-894/PDE%202035_Caderno_Demanda_Eletricidade_rev_mme_20250914.pdf

- **A demanda de eletricidade associada à eletromobilidade (TODOS os modais: leves + ônibus + caminhões) deve crescer de 627 GWh em 2025 para 7,8 TWh em 2035** — crescimento de **~12,4x** em uma década (CAGR ≈ 28,7% a.a.).
- Frota eletrificada leve (BEV+PHEV+HEV) projetada: **3,7 milhões de veículos em 2035**; **23% do licenciamento de veículos leves novos em 2035** eletrificado (≈784 mil unidades/ano).
- Ônibus: **48,5 mil ônibus eletrificados em 2035** (43,5 mil BEV puro).
- Caminhões: participação BEV de **19%** no licenciamento de semileves/leves em 2035; frota eletrificada de caminhões ≈43 mil unidades.

Fontes: PDF oficial acima; https://www.epe.gov.br/pt/imprensa/noticias/eletromobilidade-avanca-no-pais-e-pde-2035-projeta-expansao-da-eletrificacao-no-transporte-rodoviario ; https://canalve.com.br/epe-projeta-37-milhoes-ves-ruas-brasil-ate-2035/ ; https://simpleenergy.com.br/eletromobilidade-dispara-e-pode-elevar-demanda-eletrica-a-78-twh-em-2035/ ; https://eixos.com.br/transicao-energetica/quase-um-quarto-da-frota-de-novos-veiculos-leves-sera-eletrificada-em-2035-estima-epe/ (BR oficial)

**Importante — reconciliação com o relatório 01**: o valor de 7,8 TWh (2035) do PDE 2035 é **eletromobilidade TOTAL** (leves+ônibus+caminhões), enquanto o valor de 3,4 TWh (2035) da Nota Técnica EPE "Veículos Leves 2026-2035" (relatório 01, item 5b) é **apenas veículos leves BEV+PHEV**. Não são contraditórios — são escopos diferentes e coerentes entre si (3,4 TWh de leves ≈ 44% dos 7,8 TWh totais, plausível dado o consumo por veículo muito maior de ônibus/caminhões apesar do menor número de unidades).

**Limitação**: não foi possível extrair do PDF do PDE 2035 números de **pico de demanda (MW)** ou de **capacidade adicional de geração/transmissão/distribuição** necessários — o documento aparentemente cita apenas energia (GWh/TWh), não potência de pico. Recomenda-se leitura direta do PDF (ou fornecimento pelo usuário) em sessão futura com acesso a gov.br.

**Estimativa derivada (não citada por nenhuma fonte)**: combinando potência de wallbox residencial (7,4 kW) com fator de coincidência de pico internacional (15-25%), a contribuição média de cada VE ao pico coincidente do sistema seria de **~1,1 a 1,9 kW por veículo** em carregamento residencial não controlado. Tratar como hipótese de trabalho a validar, não como dado publicado.

## Tabela-resumo de parâmetros para o modelo

| Parâmetro | Valor sugerido | Origem / Confiabilidade |
|---|---|---|
| Consumo médio BEV leve (declarado) | 11-18 kWh/100km (central ~15) | INMETRO/PBEV (BR) + EPA (internacional) |
| Quilometragem média anual (Brasil) | 10.000-15.000 km/ano | Imprensa especializada BR |
| Consumo anual por veículo | **~1.800-2.200 kWh/veículo/ano** (faixa 1.300-2.700) | Estimativa derivada |
| Potência tomada comum | 1,4-2,3 kW | Referência técnica / IEA (internacional) |
| Potência wallbox monofásico | 7,4 kW | WEG WEMOB (BR) |
| Potência wallbox trifásico | 11-22 kW | IEA GEVO 2024 (internacional) |
| Potência DC rápido | 50-150 kW | WEG WEMOB (BR) |
| Potência DC ultrarrápido | 150-350 kW | IEA GEVO 2024 / Tesla-BYD BR |
| Horário de pico de conexão residencial | ~17h30-19h, decaindo até 22h-23h | NREL 2021 (internacional); coincide com ponta Light-RJ |
| Fator de coincidência no pico | 15-25% da frota (>50 VEs, 11kW) | DTU/IEEE 2021; ScienceDirect 2025 (internacional) |
| Aumento de pico — carregamento não controlado | até 20% | NREL 2021 (internacional) |
| Redução de pico — TOU aleatorizado | ~5% | NREL 2021 (internacional) |
| Redução de pico — smart charging/V1G | 6% a 66-74% (conforme escala/estudo) | Europa 2024-2026 (internacional) |
| % alimentadores exigindo reforço (>50% penetração VE, BR) | ~30% (NÃO VERIFICADO) | CBA/REASE — baixa confiabilidade |
| Tarifa Branca ANEEL — ponta | 3h consecutivas, definida por distribuidora | ANEEL REN 733/2016 (BR oficial) |
| Desconto recarga fora de ponta (Copel Mobiflex) | até 12% (recarga 0h-6h) | Copel/ANEEL 2025 (BR) |
| **Demanda elétrica eletromobilidade total (BR)** | **627 GWh (2025) → 7,8 TWh (2035)** | **EPE, PDE 2035 (BR oficial)** |
| Frota elétrica leve projetada (BR, 2035) | 3,7 milhões de veículos | EPE, PDE 2035 (BR oficial) |
| Contribuição de cada VE ao pico coincidente (não controlado) | ~1,1-1,9 kW/veículo | Estimativa derivada |

### Lacunas identificadas

1. Nenhum estudo comportamental brasileiro público (Light/Enel/CPFL/COPPE-UFRJ) com dados empíricos de horário de conexão de VEs — modelo usa proxy internacional.
2. PDE 2035 provavelmente tem curva de carga/pico assumida para eletromobilidade, não extraída nesta pesquisa (PDF ilegível pela ferramenta + bloqueio de rede).
3. "30% dos alimentadores brasileiros precisariam de reforço acima de 50% de penetração" não verificado na fonte primária.
4. Não encontradas tarifas de recarga de VE específicas de Light, Enel ou CPFL.
