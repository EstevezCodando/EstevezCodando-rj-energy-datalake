# rj-energy-datalake

Pipeline automatizado de **descoberta, coleta, versionamento, tratamento,
validação e consolidação** de dados públicos oficiais de carga e consumo
elétrico do estado do **Rio de Janeiro (RJ)** — ANEEL (CTR Curva de Carga e
SAMP Balanço), ONS (Carga de Energia Verificada), CCEE (Consumo Horário por
Perfil de Agente) e EPE (Consumo Mensal de Energia Elétrica).

Este projeto implementa a especificação recebida (`PROMPT_CRAWLER_CONSUMO_HORARIO_RJ.md`)
como um sistema de ingestão contínua e auditável, não como um script
descartável.

## ✅ Estado atual: coleta real executada com sucesso (ANEEL, ONS, SAMP, EPE)

O ambiente de execução inicialmente bloqueava o acesso de saída aos domínios
das fontes oficiais; depois de liberado (ver histórico), a coleta real foi
executada com sucesso contra 4 das 5 fontes:

- **ANEEL CTR** (consumidor-tipo + redes-tipo, Parquet, ~59 MB), **ANEEL
  SAMP Balanço** (Parquet), **ONS Carga de Energia Verificada** (API real,
  4 janelas mensais 2026-06 a 2026-09, área `RJ`) e **EPE Consumo Mensal**
  (XLSX, descoberto por scraping real da página de publicação) foram
  baixados, validados (gate de promoção aprovado) e transformados —
  `data/gold/` contém os artefatos reais resultantes (`rj_load_30min.parquet`,
  `rj_load_hourly.parquet`, `rj_average_24h*.csv`, `data_quality_report.csv`,
  `data_freshness_report.csv`).
- **CCEE está indisponível a partir deste ambiente**: `dadosabertos.ccee.org.br`
  responde `403 Forbidden` com uma página "Acesso bloqueado" — confirmado que
  é um bloqueio do **próprio WAF da CCEE** (mesmo resultado com User-Agent de
  navegador comum), não do proxy do ambiente. O crawler CCEE está implementado
  e testado com fixtures, mas a coleta real dessa fonte específica depende de
  acesso a partir de uma rede não bloqueada pela CCEE. O pipeline trata essa
  falha de forma isolada (`source_unavailable` no freshness report) sem
  impedir a coleta das demais fontes.
- 34 testes automatizados continuam passando (`pytest`) e `ruff check` está
  limpo.

### Achados reais que confirmam decisões de design da spec

- O schema real da API ONS difere do dicionário da especificação: o campo é
  `val_cargaglobalsmmgd` (não `val_cargaglobalsmmg`), há um campo adicional
  `din_atualizacao`, e `val_consistencia` vem como código numérico, não texto
  — confirmando a necessidade de nunca hardcodar schema sem inspecionar a
  fonte real (spec seção 16, aplicado por analogia ao ONS).
- No arquivo ANEEL CTR consumidor-tipo real, `DscDemandante` contém **códigos
  opacos** (`CT-001`, `CT-068`, etc. — 116 valores distintos), não rótulos como
  "Residencial"/"Industrial"; mapear esses códigos exige o dicionário de dados
  em PDF publicado junto ao dataset (ainda não baixado/parseado neste
  pipeline — ver Limitações). Isso comprova por que a spec exige nunca
  hardcodar essas categorias antes de inspecionar os valores reais.
- Entre as 62 distribuidoras (`SigCcs`) do arquivo nacional, `LIGHT` aparece
  com esse nome, mas a Enel RJ aparece como **`AMPLA`** — seu nome histórico
  (Ampla Energia e Serviços) — não como "ENEL RJ". Isso confirma exatamente a
  advertência da spec seção 20 sobre mudanças históricas de nome de
  distribuidoras que não devem ser assumidas a priori.

## 1. Arquitetura

```text
config/sources.yaml   -> pontos de partida conhecidos, package ids CKAN,
                          janelas de rechecagem, preferência de formato
src/rj_energy/
  discovery/    ckan.py (package_show), webpage.py (scraping com robots.txt)
  crawlers/     aneel_ctr.py, ons.py, ccee.py, epe.py, samp.py, base.py
  transform/    temporal.py, ons_transform.py, aneel_transform.py, epe_transform.py
  validation/   checks.py (critérios de qualidade + gate de promoção)
  lifecycle/    manifest.py (manifest central + máquina de estados)
  lineage/      lineage.py (gold_dataset_lineage)
  analytics/    curves.py (calibração estadual), metrics.py (métricas de carga)
  utils/        http.py (retry/backoff/rate-limit/robots.txt), hashing.py, logging.py
  orchestration.py  -> liga tudo (usado pela CLI)
  cli.py        -> comandos da CLI
data/
  raw/ bronze/ silver/ gold/ metadata/ quarantine/
tests/          -> fixtures gravadas + testes automatizados
```

## 2. Fontes, URLs e APIs

| Fonte | Descoberta | Uso principal |
| --- | --- | --- |
| ANEEL CTR Curva de Carga | CKAN `package_show` (`package_id=2594ebad-1306-49d1-9f30-ded144acca87`) | Forma da curva por distribuidora/classe/subgrupo/tipo de dia |
| ANEEL SAMP Balanço | CKAN `package_show` (`package_id=3193ebab-81b3-406e-be0e-f968a4a21689`) | Controle/validação de balanço energético por distribuidora |
| ONS Carga de Energia Verificada | CKAN (documentação) + API `apicarga.ons.org.br/prd/cargaverificada` | Comportamento físico semi-horário da área geoelétrica RJ |
| CCEE Consumo Horário por Perfil de Agente | CKAN `package_show` (`package_id=3d9084b8-47a8-43b1-8ce4-6d02abcd64d8`) | Consumo horário por agente/perfil/distribuidora |
| EPE Consumo Mensal de Energia Elétrica | scraping da página de publicação (não é CKAN) | Energia mensal total por UF/classe, usada para calibração |

Todos os endpoints, package ids e URLs conhecidas estão centralizados em
`config/sources.yaml` — **nada é hardcodado na lógica do pipeline**. A
descoberta dinâmica (CKAN `package_show` ou scraping da página) é sempre
tentada primeiro; as URLs conhecidas em `sources.yaml` são usadas apenas como
*fallback* explícito e logado (`fallback_used` / `known_url_fallback`).

## 3. Modelo de dados

### Manifest central (`data/metadata/manifest.parquet`)

Uma linha por versão de cada recurso baixado: `source`, `dataset`,
`package_id`, `resource_id`, `resource_name`, `reference_period`, `format`,
`download_url`, `source_published_at`, `source_modified_at`, `retrieved_at`,
`hash_sha256`, `etag`, `last_modified_http`, `file_size`, `schema_hash`,
`row_count`, `validation_status`, `lifecycle_status`, `is_latest_downloaded`,
`is_latest_valid`, `is_active_for_gold`, `processing_version`.

Nenhuma linha é apagada ou sobrescrita — novas versões são sempre *append*
(`rj_energy.lifecycle.manifest.append_entry`).

### Ciclo de vida (`LifecycleStatus`, em `models.py`)

```text
discovered → downloaded → raw_immutable → parsed → validated → normalized
→ silver → cross_validated → active (GOLD) → superseded / reprocessed
                            ↘ invalid → quarantined
```

### Tipos de observação (`ObservationType`)

`observed` | `aggregated` | `estimated` | `calibrated` | `interpolated` | `derived`
— toda tabela GOLD carrega essa distinção explicitamente; nunca são
misturados silenciosamente.

### Escopo geográfico (`GeographicScope` / `GeographicPrecision`)

`RJ_state`, `distribution_area`, `ONS_load_area`, `agent`, `connection_point`,
`multi_state_distributor` — grandezas de escopos diferentes nunca são somadas
automaticamente. Em particular, a área geoelétrica `RJ` do ONS é tratada como
`ONS_load_area` com precisão `approximate` em relação ao limite administrativo
estadual (spec seção 2.2/21).

## 4. Metodologia de atualização (dado mais atual vs. mais correto)

A cada execução de `download`: descobre → compara com o manifest → baixa →
preserva o RAW original (imutável, nunca sobrescrito) → calcula hash →
detecta revisão (hash diferente para o mesmo `resource_id`/`reference_period`).

A cada execução de `validate`: roda as checagens de qualidade
(`rj_energy.validation.checks`) e aplica o **gate de promoção**
(`rj_energy.lifecycle.manifest.evaluate_gate` / `apply_gate_decision`): uma
versão só é promovida a `active` (GOLD) se **todas** as checagens de
severidade `error` passarem. Caso contrário, fica `quarantined` e a versão
GOLD anterior **continua ativa** — a camada GOLD sempre reflete
`latest_valid_complete_version`, nunca `latest_downloaded_version`.

## 5. Freshness (`data/gold/data_freshness_report.csv`)

Classificação por fonte (`fresh` / `expected_lag` / `stale` /
`source_unavailable` / `new_version_pending_validation`), considerando a
frequência de publicação esperada de cada fonte (`EXPECTED_FRESHNESS_LAG_DAYS`
em `orchestration.py`) — nunca apenas a idade absoluta do arquivo.

## 6. Lineage (`data/metadata/gold_dataset_lineage.parquet`)

Relaciona cada produto GOLD às versões exatas das fontes usadas
(`gold_dataset`, `gold_version`, `source`, `resource_id`, `source_hash`,
`reference_period`, `pipeline_version`, `created_at`).

## 7. Detecção e tratamento de revisões históricas

`rj_energy.crawlers.base.download_and_register` compara o hash SHA-256 do
novo download com o hash mais recente já registrado para o mesmo
`resource_id`/`reference_period`. Se diferente, grava uma linha em
`source_revision_log` (`data/gold/source_revision_log.csv`) — a versão antiga
nunca é destruída.

O ONS é reconsultado periodicamente mesmo para períodos já baixados
(`recheck_windows.ons: 90d` em `config/sources.yaml`), pois a própria fonte
revisa dados recentes após a publicação inicial.

## 8. Cobertura temporal e geográfica

- Timestamps normalizados para `America/Sao_Paulo` via `zoneinfo` (banco de
  fusos do sistema), que trata corretamente os deslocamentos históricos de
  horário de verão brasileiro (abolido em 2019) — nunca por subtração fixa de
  3 horas (testado em `tests/test_temporal.py`, inclusive para datas de 2015
  ainda sob horário de verão).
- `day_type` classificado como `holiday` > `saturday` > `sunday` > `weekday`
  (feriado tem precedência), usando calendário nacional + estadual do RJ via
  a biblioteca `holidays`.
- Geograficamente, a área ONS `RJ` **não é assumida como equivalente** ao
  limite administrativo do estado; ver seção 3 acima.

## 9. Diferenças entre ONS, CCEE, ANEEL e EPE

| Fonte | Granularidade | Natureza | Uso recomendado |
| --- | --- | --- | --- |
| ONS | 30 min, área geoelétrica | `observed` | Comportamento físico real do sistema |
| CCEE | horário, por agente/perfil | `observed`/`aggregated` | Consumo por agente/distribuidora |
| ANEEL CTR | horária, por distribuidora/classe | `observed`/`aggregated` (forma) | Forma da curva por classe de consumidor |
| EPE | mensal, por UF/classe | `observed` (energia total) | Calibração de volume mensal |

Divergências entre fontes **nunca são forçadas a coincidir**: os valores
originais são preservados, o escopo é explicitado, e a divergência é
reportada em `source_comparison.csv` (spec seção 40).

## 10. Metodologia da curva estadual (`rj_energy.analytics.curves`)

Duas famílias, nunca misturadas:

- **A — observadas**: direto de ONS/CCEE.
- **B — estimadas para o estado**: forma normalizada do ANEEL CTR
  (`f_h = P_h / mean(P_0..P_23)`), calibrada pela energia mensal da EPE
  (`P_month_avg = E_month_MWh / hours_in_month`, `P_RJ_h = f_h * P_month_avg`),
  ponderada pelo número real de dias úteis/sábados/domingos/feriados do mês.
  Meta pós-calibração: `abs(error_pct) < 1%` (testado em
  `tests/test_curve_calibration.py`).

## 11. Limitações conhecidas (spec seção 41)

1. **CCEE não pôde ser coletado** neste ambiente: `dadosabertos.ccee.org.br`
   bloqueia a requisição com `403`/"Acesso bloqueado" mesmo com User-Agent de
   navegador — é um bloqueio da própria CCEE (WAF/anti-bot ou geo/IP), não do
   ambiente de execução. A descoberta de todos os meses via CKAN está
   implementada, assim como a extração best-effort do período a partir do
   nome do recurso (`extract_reference_period`, testado), mas o *parsing*
   completo do schema (detecção de schema drift coluna a coluna, dedup pela
   chave do dicionário) ainda não foi implementado — apenas a camada de
   descoberta e download. É o próximo passo natural em
   `transform/ccee_transform.py` (não criado ainda), a ser validado assim que
   houver acesso de rede que a CCEE não bloqueie.
2. **ANEEL CTR é um arquivo nacional**: o `consumidor-tipo` baixado cobre 62
   distribuidoras do Brasil inteiro, não apenas o RJ. O filtro para RJ deve
   usar `SigCcs in {"LIGHT", "AMPLA"}` — `AMPLA` é o nome histórico sob o qual
   a Enel RJ aparece nesse dataset (ver seção "Achados reais" acima); esse
   filtro ainda não está aplicado automaticamente na camada GOLD (a tabela
   `aneel_ctr_curve_stats.parquet` em `data/silver/` permanece nacional/todas
   as distribuidoras — o recorte para RJ é responsabilidade do consumidor da
   SILVER até que um filtro dedicado seja adicionado a `orchestration.py`).
   Além disso, `DscDemandante` usa códigos opacos (`CT-XXX`) cujo significado
   depende do dicionário de dados em PDF do dataset, ainda não baixado nem
   parseado por este pipeline.
3. **SAMP**: implementado apenas até a camada de download/manifest; o
   *parsing* e as checagens cruzadas de balanço energético (spec seção 19)
   ainda não têm um módulo de transform dedicado.
4. **EPE**: a descoberta por scraping da página de publicação está
   implementada com *fallback* para a URL XLSX conhecida; a comparação de
   `DataVersao` interna (spec seção 18) está parcialmente implementada em
   `transform/epe_transform.py` — falta ligá-la ao fluxo de detecção de
   revisão do manifest (hoje a revisão só é detectada por hash de arquivo).
5. **`rj_residential_average_24h.csv`** e **`source_comparison.csv`**
   dependem de um rótulo de classe residencial e de métricas equivalentes
   entre fontes que só podem ser confirmados **depois** de inspecionar os
   valores reais de `DscDemandante` (ANEEL) e os campos do CCEE/ONS — por
   isso `orchestration.build_residential_report` recebe o rótulo como
   parâmetro explícito, resolvido a partir de `distinct_category_values()`,
   em vez de hardcodá-lo (conforme exigido pela spec seção 16), mas isso
   exige uma etapa manual/orientada por CLI ainda não automatizada por
   completo.
6. **Reprocessamento incremental por partição** (spec seção 25) está
   parcialmente coberto: o `source_revision_log` detecta a revisão e o gate
   de promoção impede que uma versão inválida substitua a GOLD, mas não há
   ainda um orquestrador de DAG que recalcule automaticamente apenas as
   camadas dependentes de uma partição específica — hoje `transform` e
   `build-gold` reprocessam a partir de todos os arquivos
   `is_latest_downloaded` de cada fonte.
7. **Playwright** não foi necessário — todas as fontes usadas (CKAN JSON, API
   JSON, XLSX estático) são acessíveis via HTTP simples; a dependência não
   foi incluída para manter o projeto mais leve.
8. **`rj_residential_average_24h.csv` e `source_comparison.csv` ainda não
   foram gerados com dados reais** nesta execução — dependem dos pontos 2 e 3
   acima (rótulo de classe residencial via dicionário ANEEL, e dedup/parse do
   CCEE) e ficam para uma próxima iteração.
9. **Reprocessamento automático de partições e o `EXPECTED_FRESHNESS_LAG_DAYS`**
   usam limiares fixos (dias) como aproximação inicial; refinar com base na
   frequência real observada de publicação de cada fonte é um próximo passo.

## 12. Como rodar

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Descobrir recursos publicados agora (sem baixar nada)
python -m rj_energy discover

# Rodar o pipeline completo (download -> validate -> transform -> build-gold -> freshness -> revisions)
python -m rj_energy run-all --start-date 2026-01-01 --end-date 2026-06-30

# Rodar testes
pytest -q
```

### Exemplos DuckDB

```sql
INSTALL parquet; LOAD parquet;

-- Curva média horária observada (ONS)
SELECT hour, avg(load_hourly_mw) AS avg_mw
FROM 'data/gold/rj_load_hourly.parquet'
GROUP BY hour ORDER BY hour;

-- Manifest: versões atualmente ativas na GOLD
SELECT source, dataset, resource_id, reference_period, retrieved_at
FROM 'data/metadata/manifest.parquet'
WHERE is_active_for_gold;

-- Revisões históricas detectadas
SELECT * FROM 'data/gold/source_revision_log.csv' ORDER BY detected_at DESC;
```

## 13. Licença

MIT — ver `LICENSE`.
