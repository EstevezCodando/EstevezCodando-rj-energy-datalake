"""Cenários anuais de frota e demanda elétrica de veículos elétricos leves
(BEV+PHEV) — Brasil e Rio de Janeiro, 2026-2035.

Metodologia (ver README.md e research/*.md para fontes completas):

- **Conservador**: cenário de referência da EPE (Nota Técnica "Demanda de
  Energia dos Veículos Leves: 2026-2035", publicada 09/03/2026) — único
  cenário com 3 pontos publicados diretamente (2026, 2030, 2035), interpolado
  por crescimento composto (exponencial) entre os pontos.
- **Acelerado**: cenário "turbo eletrificação" da própria EPE (Nota Técnica
  anterior, 2025-2034), que só publicou 1 ponto (2034: 5,0 TWh). Aplicamos a
  razão turbo/referência observada em 2034 a TODOS os anos do cenário
  conservador — ou seja, um multiplicador constante, não uma curva de
  crescimento própria. Isso é uma simplificação explícita: assumimos que a
  diferença relativa entre os dois cenários da EPE se mantém proporcional ao
  longo do tempo, na ausência de mais pontos publicados do cenário turbo.
- **Intermediário**: média geométrica ano a ano entre conservador e
  acelerado — um cenário de compromisso, não uma fonte própria.

Nenhum desses cenários é "a verdade" — são todos estimativas da própria EPE
(exceto o intermediário, que é uma construção deste modelo). O objetivo é dar
um intervalo defensável, não um número único falsamente preciso.
"""

from __future__ import annotations

import math
from pathlib import Path

import polars as pl
import yaml

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "assumptions.yaml"


def load_assumptions(path: Path | None = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _exponential_interpolate(anchors: dict[int, float], year: int) -> float:
    """Interpola entre pontos-âncora (ano -> valor) assumindo crescimento
    composto (log-linear) entre eles — apropriado para séries de energia/frota,
    que tipicamente crescem multiplicativamente, não linearmente."""
    years = sorted(anchors)
    if year in anchors:
        return anchors[year]
    if year <= years[0]:
        y0, y1 = years[0], years[1]
    elif year >= years[-1]:
        y0, y1 = years[-2], years[-1]
    else:
        y0 = max(y for y in years if y <= year)
        y1 = min(y for y in years if y >= year)
    v0, v1 = anchors[y0], anchors[y1]
    if v0 <= 0 or v1 <= 0:
        # fallback linear se algum ponto for zero (log indefinido)
        frac = (year - y0) / (y1 - y0)
        return v0 + frac * (v1 - v0)
    log_v0, log_v1 = math.log(v0), math.log(v1)
    frac = (year - y0) / (y1 - y0)
    return math.exp(log_v0 + frac * (log_v1 - log_v0))


def national_light_ev_scenarios(assumptions: dict | None = None) -> pl.DataFrame:
    """Demanda elétrica nacional para recarga de veículos leves BEV+PHEV,
    2026-2035, nos 3 cenários (spec: 'trabalhar com diferentes cenários —
    conservador, intermediário e acelerado')."""
    cfg = assumptions or load_assumptions()
    years = cfg["meta"]["horizon_years"]
    national_ev = cfg["national_ev"]

    reference_anchors = {int(y): v for y, v in national_ev["demand_light_only_reference_twh"].items()}
    turbo_year = 2034
    turbo_demand_twh = national_ev["third_party"]["epe_turbo_2034_demand_twh"]
    reference_at_turbo_year = _exponential_interpolate(reference_anchors, turbo_year)
    turbo_multiplier = turbo_demand_twh / reference_at_turbo_year

    kwh_per_vehicle_central = cfg["charging_behavior"]["avg_annual_consumption_kwh_per_vehicle"]["central"]

    rows = []
    for year in years:
        conservative_twh = _exponential_interpolate(reference_anchors, year)
        accelerated_twh = conservative_twh * turbo_multiplier
        intermediate_twh = math.sqrt(conservative_twh * accelerated_twh)  # média geométrica

        for scenario, demand_twh in (
            ("conservador", conservative_twh),
            ("intermediario", intermediate_twh),
            ("acelerado", accelerated_twh),
        ):
            value_type = "observed_anchor" if year in reference_anchors and scenario == "conservador" else (
                "derived_constant_ratio" if scenario == "acelerado" else
                "derived_geometric_mean" if scenario == "intermediario" else
                "interpolated_exponential"
            )
            implied_fleet_units = demand_twh * 1e9 / kwh_per_vehicle_central
            rows.append({
                "year": year,
                "scenario": scenario,
                "region": "brasil",
                "demand_light_ev_twh": round(demand_twh, 4),
                "implied_bev_phev_fleet_units": round(implied_fleet_units),
                "value_type": value_type,
            })

    return pl.DataFrame(rows).sort(["scenario", "year"])


def rj_weight_bounds(assumptions: dict | None = None) -> tuple[float, float]:
    """Faixa de participação do RJ na frota nacional de VEs leves (BEV+PHEV).

    Não existe projeção nem participação oficial publicada para o RJ (spec:
    'não encontrado' na pesquisa) — por isso usamos uma FAIXA, não um número
    único, delimitada por duas razões observadas com escopos ligeiramente
    diferentes (documentado em detalhe no README):

    - limite inferior: RJ (39.295, jan/2026) / frota nacional "eletrificados"
      em escopo amplo incl. HEV (1.000.000, set/2026) ≈ 3,9%
    - limite superior: RJ (39.295, jan/2026) / frota circulante nacional
      BEV+PHEV, escopo mais próximo do usado nos cenários (395.000, 2024) ≈ 9,9%
    """
    cfg = assumptions or load_assumptions()
    rj = cfg["rj_ev"]["state_fleet_2026_01_units"]
    national_broad = cfg["national_ev"]["cumulative_electrified_broad_2026_09_units"]
    national_bev_phev = cfg["national_ev"]["circulating_bev_phev_2024_units"]
    low = rj / national_broad
    high = rj / national_bev_phev
    return (low, high)


def rj_historical_cagr(assumptions: dict | None = None) -> float:
    """CAGR observado da frota de VEs do próprio estado do RJ, 2021-2025
    (Detran-RJ: 3.263 -> 30.000+). Crescimento local explosivo de base baixa —
    NÃO deve ser extrapolado linearmente até 2035 (resultaria em números
    absurdos); usado apenas como checagem de plausibilidade de curto prazo,
    nunca como o cenário principal."""
    cfg = assumptions or load_assumptions()
    rj = cfg["rj_ev"]
    start, end = rj["state_fleet_2021_units"], rj["state_fleet_2025_units"]
    n_years = 4
    return (end / start) ** (1 / n_years) - 1


def rj_ev_scenarios(national_df: pl.DataFrame | None = None, assumptions: dict | None = None) -> pl.DataFrame:
    """Projeção de demanda/frota de VEs para o RJ, derivada proporcionalmente
    da curva nacional (spec seção 8: 'não encontrado' localmente -> derivar
    proporcionalmente, deixando isso explícito)."""
    cfg = assumptions or load_assumptions()
    national = national_df if national_df is not None else national_light_ev_scenarios(cfg)
    weight_low, weight_high = rj_weight_bounds(cfg)
    weight_central = math.sqrt(weight_low * weight_high)

    rows = []
    for row in national.iter_rows(named=True):
        for weight_label, weight in (("low", weight_low), ("central", weight_central), ("high", weight_high)):
            rows.append({
                "year": row["year"],
                "scenario": row["scenario"],
                "rj_weight_case": weight_label,
                "region": "rio_de_janeiro",
                "demand_light_ev_twh": round(row["demand_light_ev_twh"] * weight, 5),
                "implied_bev_phev_fleet_units": round(row["implied_bev_phev_fleet_units"] * weight),
                "value_type": "derived_proportional_national_share",
            })

    return pl.DataFrame(rows).sort(["scenario", "rj_weight_case", "year"])


def pde2035_all_modes_reference(assumptions: dict | None = None) -> pl.DataFrame:
    """Série de contexto (NÃO um dos 3 cenários de veículos leves): demanda de
    eletromobilidade TOTAL (leve + ônibus + caminhão) segundo o PDE 2035 da
    EPE — 627 GWh (2025) -> 7,8 TWh (2035), interpolado exponencialmente."""
    cfg = assumptions or load_assumptions()
    anchors = {int(y): v for y, v in cfg["national_ev"]["demand_all_modes_pde2035_twh"].items()}
    years = cfg["meta"]["horizon_years"]
    rows = [
        {
            "year": year,
            "demand_all_modes_twh": round(_exponential_interpolate(anchors, year), 4),
            "value_type": "observed_anchor" if year in anchors else "interpolated_exponential",
        }
        for year in years
    ]
    return pl.DataFrame(rows)
