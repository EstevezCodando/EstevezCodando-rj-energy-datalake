# Resumo executivo — Projeção de Demanda Elétrica por Eletrificação Veicular (2035)

_Gerado em 2026-09-26T02:57:43.696997+00:00. Ver `README.md` deste módulo para metodologia completa e `research/` para as fontes primárias._

## Cenários nacionais — demanda de recarga de veículos leves (BEV+PHEV), 2035

| Cenário | Demanda (TWh) | Frota implícita (BEV+PHEV) |
|---|---|---|
| conservador | 3.40 | 1,700,000 |
| intermediario | 4.39 | 2,196,924 |
| acelerado | 5.68 | 2,839,104 |

Para contexto (não comparável diretamente — escopo mais amplo, todos os modais): o PDE 2035 da EPE projeta **7.80 TWh** em 2035 para TODA a eletromobilidade (leves + ônibus + caminhões), partindo de 0,627 TWh em 2025.

**Checagem de consistência**: a frota implícita do cenário acelerado em 2035 (2,839,104 veículos BEV+PHEV, derivada da energia) equivale a **77%** da frota oficial de leves eletrificados projetada pela EPE para 2035 (3,700,000 veículos, PDE 2035 — inclui também HEV não-plugável). Como HEV não consome eletricidade da rede, esperar uma fração menor que 100% é o resultado esperado, não um erro do modelo.

## Rio de Janeiro (derivado proporcionalmente — sem projeção estadual publicada)

Peso do RJ na frota nacional de BEV+PHEV: **3.9% a 9.9%** (faixa por ambiguidade de escopo entre fontes — ver README).
CAGR histórico observado da frota do próprio RJ (2021-2025, Detran-RJ): **74% a.a.** — explosivo por partir de base baixa; NÃO extrapolado linearmente até 2035 (ver README).

| Cenário | Peso RJ | Demanda RJ 2035 (TWh) | Frota implícita RJ 2035 |
|---|---|---|---|
| conservador | low | 0.1336 | 66,802 |
| conservador | central | 0.2126 | 106,289 |
| conservador | high | 0.3382 | 169,118 |
| intermediario | low | 0.1726 | 86,328 |
| intermediario | central | 0.2747 | 137,358 |
| intermediario | high | 0.4371 | 218,552 |
| acelerado | low | 0.2231 | 111,563 |
| acelerado | central | 0.3550 | 177,509 |
| acelerado | high | 0.5649 | 282,437 |

## Impacto na curva de carga real do RJ em 2035

Curva base: `data/gold/rj_average_24h.csv` (observada, coletada do ONS por este mesmo datalake). Dois casos: **central** (cenário intermediário, peso RJ central — resultado mais provável) e **upper_bound** (cenário acelerado, peso RJ alto — pior caso razoável). Frota usada: central=137,358 veículos, upper_bound=282,437 veículos.

| Caso | Estratégia | Pico base (MW) | Hora pico base | Novo pico (MW) | Nova hora pico | Aumento do pico (%) | Pico mudou de hora? |
|---|---|---|---|---|---|---|---|
| central | uncontrolled | 6077 | 19h | 6171 | 19h | 1.55% | não |
| central | smart | 6077 | 19h | 6135 | 19h | 0.96% | não |
| central | offpeak_shifted | 6077 | 19h | 6077 | 19h | 0.00% | não |
| upper_bound | uncontrolled | 6077 | 19h | 6271 | 19h | 3.18% | não |
| upper_bound | smart | 6077 | 19h | 6197 | 19h | 1.97% | não |
| upper_bound | offpeak_shifted | 6077 | 19h | 6077 | 19h | 0.00% | não |

**Leitura**: o pico real observado do sistema RJ ocorre às 19h (ver `data/gold/rj_average_24h.csv`), exatamente dentro da janela em que a pesquisa (NREL 2021; tarifa de ponta Light-RJ, 17h30-20h30) aponta como o horário típico de conexão residencial de VEs. Carregamento não controlado tende a empilhar-se sobre o pico já existente; deslocar a recarga para a madrugada (ex.: piloto Copel Mobiflex, 00h-06h) elimina esse efeito por construção.
