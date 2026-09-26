# Projeção de Demanda Elétrica por Eletrificação Veicular — Brasil e RJ (2026-2035)

Modelo de projeção da demanda elétrica adicional gerada pela eletrificação da
frota veicular no Brasil, com foco no Rio de Janeiro, até 2035. Construído
sobre os dados **reais** já coletados por este mesmo datalake (`data/gold/`)
combinados com pesquisa dedicada de dados públicos sobre frota de veículos
elétricos (VEs), setor elétrico e comportamento de carregamento.

## Por que este módulo existe

O objetivo é responder: **quanto da nova demanda elétrica até 2035 pode ser
atribuída aos veículos elétricos, e qual o impacto dessa eletrificação sobre
a rede elétrica do RJ?** — separando sempre dados observados, premissas de
terceiros e estimativas derivadas por este modelo.

## Estrutura

```text
research/       -> relatórios de pesquisa (fonte + ano + classificação), imutáveis
config/
  assumptions.yaml  -> TODOS os parâmetros do modelo, com fonte citada em comentário
src/
  scenarios.py      -> cenários anuais de frota/demanda (nacional + RJ), 2026-2035
  charging_impact.py -> impacto horário na curva de carga real do RJ
  run_report.py     -> gera todos os CSVs + o resumo executivo
tests/          -> testes automatizados da lógica de cenários e impacto
output/         -> CSVs e RESUMO_EXECUTIVO.md gerados (reprodutíveis, não editar à mão)
```

## Como rodar

```bash
# a partir da raiz do repositório rj-energy-datalake, com o venv principal ativo
# (usa as mesmas dependências: polars, pyyaml — já instaladas)
python projections/ev_demand_2035/src/run_report.py

# rodar os testes deste módulo (incluídos no pytest principal)
pytest projections/ev_demand_2035/tests -v
```

Gera em `output/`:
- `scenarios_national_light_ev.csv` — frota/demanda nacional, 3 cenários, 2026-2035
- `scenarios_rj_light_ev.csv` — idem para o RJ (3 pesos de participação × 3 cenários)
- `context_pde2035_all_modes.csv` — série de contexto (eletromobilidade total, PDE 2035)
- `grid_impact_summary_2035.csv` / `hourly_load_by_strategy_2035.csv` — impacto horário
- `RESUMO_EXECUTIVO.md` — leitura rápida de tudo acima

## Metodologia

### 1. Fontes primárias e pesquisa

Toda pesquisa foi feita por agentes dedicados (WebSearch/WebFetch) em
2026-09-26 e está preservada, imutável, em `research/`:

- `research/01_frota_ve_setor_eletrico_br_rj.md` — consumo/geração elétrica
  BR, frota de VEs BR/RJ, projeções setoriais (EPE, ABVE, IEA, consultoria
  Bright).
- `research/02_carregamento_impacto_rede.md` — consumo por veículo, potências
  de carregamento, horários de conexão, fator de coincidência, impacto em
  transformadores, estratégias de carregamento, tarifas brasileiras.

Cada afirmação nesses arquivos é classificada como **observado** (dado
publicado diretamente), **estimativa de terceiros** (projeção publicada por
alguém, não por este modelo) ou **estimativa derivada** (calculada neste
relatório, sem citação direta). `config/assumptions.yaml` referencia essas
classificações em comentários.

### 2. Cenários de veículos leves (BEV+PHEV) — nacional

Três cenários, **todos ancorados em números publicados pela própria EPE**
(nunca inventados por este modelo):

| Cenário | Âncora(s) publicada(s) | Como o modelo preenche os anos entre âncoras |
|---|---|---|
| **Conservador** | EPE, Nota Técnica "Veículos Leves 2026-2035": 0,7 TWh (2026), 1,8 TWh (2030), 3,4 TWh (2035) | Interpolação por crescimento composto (log-linear) entre âncoras |
| **Acelerado** | EPE, cenário "turbo eletrificação" (Nota Técnica anterior, 2025-2034): 5,0 TWh em 2034 (único ponto publicado) | Razão turbo/referência em 2034 aplicada como multiplicador constante sobre TODO o cenário conservador |
| **Intermediário** | — (construção deste modelo) | Média geométrica, ano a ano, entre conservador e acelerado |

**Por que um multiplicador constante para o acelerado, e não uma curva
própria?** Porque a EPE só publicou 1 ponto do cenário turbo (2034). Com um
único ponto não é possível ajustar uma curva de crescimento própria sem
inventar uma forma — a simplificação mais honesta é assumir que a diferença
relativa entre os dois cenários da EPE se mantém proporcional ao longo do
tempo. Isso é uma limitação explícita, não escondida.

**Métrica de contexto, fora dos 3 cenários**: o PDE 2035 (mais recente e mais
oficial que a Nota Técnica) projeta a demanda de **toda** a eletromobilidade
(leves + ônibus + caminhões) crescendo de 0,627 TWh (2025) para **7,8 TWh
(2035)**. Não é comparável diretamente aos 3 cenários acima (que cobrem só
veículos leves BEV+PHEV) — reportado em `context_pde2035_all_modes.csv` e no
resumo executivo como checagem de ordem de grandeza, não como um 4º cenário.

**Checagem de consistência interna**: o modelo converte cada cenário de TWh
para "frota implícita de BEV+PHEV" usando o consumo médio anual por veículo
assumido (~2.000 kWh/veículo/ano, estimativa derivada — ver seção 4). Essa
frota implícita do cenário acelerado em 2035 deve ficar **abaixo** da frota
oficial de "leves eletrificados" da EPE para 2035 (3,7 milhões, que inclui
HEV não-plugável, o qual não consome eletricidade da rede) — o
`RESUMO_EXECUTIVO.md` reporta essa razão a cada execução como um alarme
automático caso as premissas fiquem inconsistentes.

### 3. Rio de Janeiro — derivação proporcional

**Não existe nenhuma projeção de frota de VE publicada especificamente para o
RJ** (confirmado pela pesquisa — ver `research/01` item 8). O modelo:

1. Calcula o **peso atual do RJ na frota nacional de BEV+PHEV**, como uma
   **faixa** (não um número único, por ambiguidade de escopo entre as
   fontes disponíveis):
   - limite inferior (~3,9%): RJ (39.295 veículos, jan/2026) ÷ frota nacional
     "eletrificados" em escopo amplo incluindo HEV (1.000.000, set/2026);
   - limite superior (~9,9%): RJ (39.295) ÷ frota circulante nacional
     BEV+PHEV, escopo mais próximo do usado nos cenários (395.000, 2024).
2. Aplica essa faixa de peso (baixo/central/alto, sendo central a média
   geométrica) sobre a curva nacional de demanda, para cada um dos 3
   cenários — resultando em 9 combinações (3 cenários × 3 pesos).
3. Reporta, à parte, o **CAGR histórico observado da própria frota do RJ**
   (Detran-RJ: 3.263 em 2021 → mais de 30.000 em 2025 → 74% a.a.) como
   checagem de plausibilidade de curto prazo — **explicitamente não
   extrapolado linearmente até 2035**, pois um crescimento de 74% a.a. por 10
   anos resultaria em números fisicamente implausíveis (é crescimento típico
   de adoção inicial em base muito baixa, que tende a desacelerar).

### 4. Comportamento de carregamento e impacto na curva de carga

- **Consumo por veículo**: ~1.800-2.200 kWh/veículo/ano (estimativa derivada:
  eficiência declarada PBEV/INMETRO de VEs populares no Brasil, 11-18
  kWh/100km, × quilometragem média anual brasileira, 10.000-15.000 km/ano).
- **Potências de carregamento**: tomada comum (1,4-2,3 kW), wallbox
  monofásico (7,4 kW, padrão ABNT NBR 17019), wallbox trifásico (11-22 kW),
  DC rápido (50-150 kW), DC ultrarrápido (150-350 kW).
- **Forma da curva horária de conexão residencial** (`charging_impact.py`,
  `uncontrolled_shape()`): pico sintético às 18h-19h, decaindo até ~23h.
  **Esta forma NÃO é uma curva publicada** — nenhum estudo comportamental
  brasileiro (Light/Enel/CPFL/COPPE-UFRJ) foi encontrado com esse detalhe. É
  informada pela descrição qualitativa da pesquisa (NREL 2021: pico de
  conexão "17h30-19h decaindo até 22h-23h") e pelo fator de coincidência
  quantitativo (DTU/IEEE 2021, ScienceDirect 2025: 15-25% da frota carregando
  simultaneamente no pico, para >50 veículos a 11kW). Tratado como
  `observation_type=estimated` em todo o código e neste README — nunca como
  dado observado.
- **Validação cruzada real importante**: o pico REAL observado da curva de
  carga do RJ, calculado a partir dos dados que este próprio datalake coletou
  do ONS, ocorre às **19h** (`data/gold/rj_average_24h.csv`). Isso coincide
  quase exatamente com (a) o horário de ponta tarifário real da Light-RJ
  (17h30-20h30) e (b) o horário internacional típico de conexão residencial
  de VEs — uma convergência de 3 fontes independentes (dado real coletado,
  tarifa real brasileira, literatura internacional) que dá razoável confiança
  à hipótese central do modelo: carregamento residencial não controlado
  tende a se sobrepor exatamente ao pico já existente do sistema.
- **3 estratégias de carregamento comparadas** (`charging_impact.py`):
  - `uncontrolled`: forma acima, sem gestão.
  - `smart`: reduz a carga nas horas de pico (17h-20h) em 6-70% (faixa da
    pesquisa, ponto médio ~38% usado), redistribuindo a energia removida
    para as demais horas — preserva o total diário de energia.
  - `offpeak_shifted`: toda a energia deslocada para 00h-06h (informado pelo
    piloto real Copel Mobiflex, que dá desconto de até 12% para recarga
    nesse horário).

### 5. O que o modelo NÃO faz (limitações explícitas)

1. **Não modela retirada de frota (sucateamento)** — a "frota implícita"
   derivada da demanda é uma frota ativa consumindo eletricidade num dado
   ano, não uma reconciliação completa de estoque (vendas acumuladas menos
   veículos retirados de circulação).
2. **A forma horária de carregamento é sintética**, informada por descrições
   qualitativas e um único parâmetro quantitativo (fator de coincidência no
   pico) — não uma curva de 24h publicada. Ver seção 4.
3. **O peso do RJ na frota nacional é uma faixa larga (3,9%-9,9%)**, não um
   número único, por ambiguidade genuína de escopo entre as fontes
   disponíveis — não reduzido artificialmente a um ponto médio único sem
   justificativa.
4. **Não modela capacidade de geração/transmissão adicional necessária em
   GW** — a pesquisa não encontrou esse número no PDE 2035 (o documento
   aparentemente só publica energia em GWh/TWh, não potência de pico
   associada à eletromobilidade). Isso é uma lacuna de dados da própria
   fonte oficial, não uma omissão deste modelo.
5. **O número "~30% dos alimentadores brasileiros precisariam de reforço
   acima de 50% de penetração de VE" não foi verificado em texto integral**
   (acesso bloqueado durante a pesquisa) — não usado como parâmetro
   quantitativo do modelo, citado apenas como referência qualitativa de risco
   em `research/02`.
6. **Este modelo cobre apenas veículos leves de passeio (BEV+PHEV)** — não
   modela ônibus nem caminhões elétricos, que o PDE 2035 já indica serem uma
   parte relevante (48,5 mil ônibus, ~43 mil caminhões elétricos projetados
   para 2035) da diferença entre os 3,4 TWh (leves, cenário conservador) e os
   7,8 TWh (todos os modais, PDE 2035) em 2035.

## Fontes principais (resumo — ver `research/*.md` para lista completa)

- EPE — Balanço Energético Nacional 2025 (ano-base 2024)
- EPE — Plano Decenal de Expansão de Energia (PDE) 2034 e PDE 2035
- EPE — Nota Técnica "Demanda de Energia dos Veículos Leves: 2026-2035" (EPE/DPG/SDB/2026/01)
- ABVE — Associação Brasileira do Veículo Elétrico (relatórios de emplacamento)
- Detran-RJ — Anuário do Trânsito (frota de VEs no estado)
- IEA — Global EV Outlook 2025
- NREL, DTU/IEEE, EPRI, ScienceDirect — literatura internacional sobre carregamento e impacto na rede
- ANEEL — Tarifa Branca (REN 733/2016); Light-RJ e Copel — tarifas/pilotos de recarga de VE
- Este mesmo datalake — `data/gold/rj_average_24h.csv` (curva real de carga do RJ, coletada do ONS)
