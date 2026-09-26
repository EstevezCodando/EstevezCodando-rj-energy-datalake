---
license: other
license_name: mixed-odbl-ccby-attribution
license_link: https://github.com/EstevezCodando/EstevezCodando-rj-energy-datalake/blob/main/README.md#13-licença
language:
- pt
tags:
- energy
- electricity
- power-grid
- time-series
- brazil
- rio-de-janeiro
- open-data
- ons
- aneel
- epe
pretty_name: RJ Energy Datalake — Carga e Consumo Elétrico do Rio de Janeiro
size_categories:
- 1K<n<10K
configs:
  - config_name: load_30min
    data_files: "gold/rj_load_30min.parquet"
  - config_name: load_hourly
    data_files: "gold/rj_load_hourly.parquet"
  - config_name: average_24h
    data_files: "gold/rj_average_24h.csv"
  - config_name: average_24h_by_day_type
    data_files: "gold/rj_average_24h_by_day_type.csv"
  - config_name: average_24h_by_month
    data_files: "gold/rj_average_24h_by_month.csv"
  - config_name: data_quality_report
    data_files: "gold/data_quality_report.csv"
  - config_name: data_freshness_report
    data_files: "gold/data_freshness_report.csv"
  - config_name: source_revision_log
    data_files: "gold/source_revision_log.csv"
  - config_name: manifest
    data_files: "metadata/manifest.parquet"
---

# RJ Energy Datalake — Carga e Consumo Elétrico do Rio de Janeiro

**English summary**: Real, continuously-updated open data on electricity load and
consumption for the state of Rio de Janeiro, Brazil, collected from Brazil's
official grid operator (ONS), electricity regulator (ANEEL) and energy
planning agency (EPE) open data portals. Includes 30-minute and hourly load
series for the ONS "RJ" load area, national tariff load-curve data (ANEEL
CTR), and monthly energy balance data (SAMP), with full provenance (manifest
with source hashes, retrieval timestamps, and lifecycle status per version).
See the [source GitHub repository](https://github.com/EstevezCodando/EstevezCodando-rj-energy-datalake)
for the full pipeline code.

## Descrição

Este dataset é a camada GOLD (produtos analíticos consolidados) do pipeline
[`rj-energy-datalake`](https://github.com/EstevezCodando/EstevezCodando-rj-energy-datalake),
que coleta, versiona, valida e consolida dados públicos oficiais de carga e
consumo elétrico do estado do Rio de Janeiro (RJ), Brasil.

Os dados são **reais**, coletados diretamente das APIs/catálogos oficiais das
fontes abaixo — nenhum valor é sintético ou inventado. Onde um dado não pôde
ser medido diretamente, isso é sinalizado explicitamente (`observation_type`,
`quality_flag`), nunca inferido silenciosamente.

## Fontes e cobertura

| Fonte | Dataset oficial | Cobertura neste dump | Licença da fonte |
| --- | --- | --- | --- |
| ONS (Operador Nacional do Sistema Elétrico) | [Carga de Energia Verificada](https://dados.ons.org.br/dataset/carga-energia-verificada) | Área geoelétrica RJ, 30 min, 2026-06-01 a 2026-09-26 | CC-BY |
| ANEEL | [CTR Curva de Carga](https://dadosabertos.aneel.gov.br/dataset/ctr-curva-de-carga) (consumidor-tipo + redes-tipo) | Nacional (62 distribuidoras, RJ incluso via `LIGHT` e `AMPLA`/Enel RJ) | ODbL (**share-alike**) |
| ANEEL | [SAMP Balanço](https://dadosabertos.aneel.gov.br/dataset/samp-balanco) | Nacional, todas as distribuidoras | ODbL (**share-alike**) |
| EPE | [Consumo Mensal de Energia Elétrica](https://www.epe.gov.br/pt/publicacoes-dados-abertos/dados-abertos/dados-do-consumo-mensal-de-energia-eletrica) | Nacional, por UF/classe | Dados abertos EPE (atribuição) |
| CCEE | Consumo Horário por Perfil de Agente | **Não incluído** — fonte bloqueou o acesso (WAF, `403`) a partir do ambiente de coleta | — |

Por combinar fontes com licenças diferentes — em particular o ANEEL CTR e
SAMP sob **ODbL**, que exige *share-alike* para bases de dados derivadas — o
uso deste dataset deve respeitar a licença mais restritiva aplicável a cada
subconjunto. Ao redistribuir uma base derivada que incorpore os dados ANEEL
(`load_hourly`/`load_30min` não dependem do ANEEL; qualquer análise futura
que junte a forma de curva ANEEL exige atenção à ODbL), mantenha a atribuição
e a mesma licença compartilhada. Sempre cite a fonte original.

## Subconjuntos (configs)

Carregue com a biblioteca `datasets`:

```python
from datasets import load_dataset

# Curva de carga observada do ONS, resolução de 30 minutos
ds = load_dataset("EstevezCodando/rj-energy-datalake", "load_30min")

# Agregado por hora (potência média MW e energia MWh)
ds_hourly = load_dataset("EstevezCodando/rj-energy-datalake", "load_hourly")

# Curva média de 24h (todas as observações agregadas por hora do dia)
ds_avg = load_dataset("EstevezCodando/rj-energy-datalake", "average_24h")
```

| Config | Arquivo | Linhas | Descrição |
| --- | --- | --- | --- |
| `load_30min` | `gold/rj_load_30min.parquet` | ~5.6k | Série bruta de 30 min do ONS (observada), área RJ, com colunas temporais padronizadas |
| `load_hourly` | `gold/rj_load_hourly.parquet` | ~2.8k | Agregação horária: `load_hourly_mw = mean(2 leituras de 30min)`, `energy_hourly_mwh = sum(energia dos 2 intervalos)` |
| `average_24h` | `gold/rj_average_24h.csv` | 24 | Curva média de 24h (todas as datas), com `normalized_load` |
| `average_24h_by_day_type` | `gold/rj_average_24h_by_day_type.csv` | 96 | Curva média por hora, separada por `day_type` (weekday/saturday/sunday/holiday) |
| `average_24h_by_month` | `gold/rj_average_24h_by_month.csv` | 96 | Curva média por hora, separada por mês |
| `data_quality_report` | `gold/data_quality_report.csv` | variável | Resultado de cada checagem de qualidade aplicada por versão de recurso |
| `data_freshness_report` | `gold/data_freshness_report.csv` | 5 | Status de atualização por fonte (`fresh`/`stale`/`source_unavailable`/...) |
| `source_revision_log` | `gold/source_revision_log.csv` | variável | Log de revisões históricas detectadas por hash |
| `manifest` | `metadata/manifest.parquet` | variável | Proveniência completa: hash SHA-256, URL, timestamps, status de ciclo de vida por versão de cada recurso baixado |

### Principais colunas — `load_hourly`

| Coluna | Tipo | Significado |
| --- | --- | --- |
| `date`, `year`, `month`, `day`, `hour` | data/int | Data e hora local (America/Sao_Paulo) |
| `day_type` | str | `weekday` \| `saturday` \| `sunday` \| `holiday` (feriados nacionais + RJ) |
| `load_hourly_mw` | float | Potência média da hora, em MW (**observed/aggregated** — nunca soma direta de MW) |
| `energy_hourly_mwh` | float | Energia da hora, em MWh |
| `n_intervals` | int | Quantos dos 2 intervalos de 30 min estavam presentes (2 = completo) |
| `quality_flag` | str | `ok` \| `incomplete_hour` — horas com menos de 2 leituras válidas nunca são silenciosamente tratadas como completas |
| `geographic_scope` / `geographic_precision` | str | `ONS_load_area` / `approximate` — a área geoelétrica "RJ" do ONS **não é idêntica** ao limite administrativo do estado |
| `observation_type` | str | `aggregated` (nunca `estimated`/`calibrated` nesta tabela — é dado medido) |

## Achados reais e cuidados de qualidade importantes

- **Placeholder de zero no intervalo mais recente**: a API do ONS retorna
  `val_cargaglobal = 0` para os 1-2 intervalos de 30 min mais recentes ainda
  não consolidados no momento da consulta — não é uma medição real (a carga
  de uma área inteira nunca é fisicamente zero). O pipeline trata isso como
  valor ausente antes de agregar, e a hora correspondente fica marcada como
  `incomplete_hour` em vez de silenciosamente errada.
- **ANEEL CTR é nacional, não filtrado para RJ**: os arquivos de curva de
  carga por consumidor-tipo cobrem 62 distribuidoras do Brasil; a Enel RJ
  aparece sob seu nome histórico **`AMPLA`**, não "ENEL RJ" — confirmado por
  inspeção direta dos dados, não assumido a priori.
- **Área ONS "RJ" ≠ limite administrativo estadual exato** — trate
  `geographic_precision = approximate` como um aviso real, não decorativo.
- **CCEE ausente**: o WAF da própria CCEE bloqueia requisições automatizadas
  a partir do ambiente de coleta (`403 Acesso bloqueado`), mesmo com
  User-Agent de navegador. O crawler existe no repositório-fonte mas os
  dados não puderam ser coletados nesta versão do dataset.

Detalhes completos de metodologia, ciclo de vida dos dados e limitações no
[README do repositório-fonte](https://github.com/EstevezCodando/EstevezCodando-rj-energy-datalake#readme).

## Atualização

Este dataset é gerado por um pipeline automatizado
(`python -m rj_energy run-all`). Consulte `data_freshness_report` para saber
a data da última coleta bem-sucedida por fonte antes de assumir que os dados
estão atualizados no momento em que você os está lendo.

## Como citar

Se usar este dataset, cite as fontes primárias (ONS, ANEEL, EPE — ver tabela
acima) e este repositório:

```
EstevezCodando (2026). RJ Energy Datalake — Carga e Consumo Elétrico do Rio de
Janeiro. https://github.com/EstevezCodando/EstevezCodando-rj-energy-datalake
```

## Licença

Ver seção "Fontes e cobertura" acima. Não há uma licença única simples porque
os dados de origem têm licenças diferentes (CC-BY, ODbL). Ao redistribuir,
mantenha a atribuição a cada fonte original e respeite a ODbL (share-alike)
para qualquer produto derivado que incorpore os dados ANEEL.
