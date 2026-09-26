"""Impacto horário do carregamento de VEs sobre a curva de carga do RJ.

Combina a curva REAL observada do sistema (data/gold/rj_average_24h.csv,
coletada do ONS por este mesmo datalake) com uma adição de carga ESTIMADA de
VEs, para as 3 estratégias de carregamento descritas na pesquisa:

- `uncontrolled`: carregamento residencial não gerenciado (a maioria conecta
  ao chegar em casa, ~17h30-19h) — spec: "carregamento não controlado".
- `smart`: carregamento inteligente (V1G) — reduz o pico coincidente,
  redistribuindo energia para outras horas mas preservando o total diário.
- `offpeak_shifted`: deslocado para a janela de menor tarifa (piloto Copel
  Mobiflex, 00h-06h) — spec: "deslocamento da recarga para horários de menor
  demanda".

⚠️ O FORMATO da curva de 24h de conexão residencial (`_connection_shape`)
é uma construção deste modelo, informada pela descrição qualitativa da
pesquisa (pico ~17h30-19h, decaindo até 22h-23h — NREL 2021) e pelo fator de
coincidência quantitativo (DTU/IEEE 2021, ScienceDirect 2025), mas NÃO é uma
curva de 24h diretamente publicada por nenhuma fonte — nenhum estudo com esse
detalhe foi encontrado para o Brasil. Tratar como `observation_type=estimated`,
nunca como `observed`.
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl
from scenarios import load_assumptions

# Pesos relativos por hora (0-23), somando 1.0 — forma sintética informada pela
# pesquisa (pico 18-19h, decaindo até ~23h; residual noturno baixo).
# NÃO é uma curva publicada — ver docstring do módulo.
_UNCONTROLLED_SHAPE_RAW = {
    0: 0.010, 1: 0.008, 2: 0.006, 3: 0.005, 4: 0.005, 5: 0.006,
    6: 0.010, 7: 0.015, 8: 0.018, 9: 0.018, 10: 0.018, 11: 0.018,
    12: 0.020, 13: 0.020, 14: 0.020, 15: 0.025, 16: 0.045, 17: 0.075,
    18: 0.100, 19: 0.095, 20: 0.080, 21: 0.065, 22: 0.048, 23: 0.030,
}


def _normalized_shape(raw: dict[int, float]) -> dict[int, float]:
    total = sum(raw.values())
    return {h: v / total for h, v in raw.items()}


def uncontrolled_shape() -> dict[int, float]:
    return _normalized_shape(_UNCONTROLLED_SHAPE_RAW)


def offpeak_shifted_shape(offpeak_start_hour: int = 0, offpeak_end_hour: int = 6) -> dict[int, float]:
    """Toda a energia deslocada para a janela fora de ponta (ex.: Copel
    Mobiflex, 00h-06h), distribuída uniformemente dentro dela."""
    hours = list(range(offpeak_start_hour, offpeak_end_hour))
    weight = 1.0 / len(hours)
    return {h: (weight if h in hours else 0.0) for h in range(24)}


def smart_charging_shape(uncontrolled: dict[int, float], peak_hours: tuple[int, ...], reduction_pct: float) -> dict[int, float]:
    """Reduz a carga nas horas de pico em `reduction_pct`% e redistribui a
    energia removida uniformemente pelas horas fora do pico, preservando o
    total diário (carregamento inteligente não reduz a energia total, apenas
    desloca no tempo — spec: 'carregamento inteligente')."""
    shape = dict(uncontrolled)
    removed = 0.0
    for h in peak_hours:
        cut = shape[h] * (reduction_pct / 100)
        shape[h] -= cut
        removed += cut
    off_peak_hours = [h for h in range(24) if h not in peak_hours]
    for h in off_peak_hours:
        shape[h] += removed / len(off_peak_hours)
    return shape


@dataclass(frozen=True)
class ChargingImpactResult:
    hourly: pl.DataFrame  # hour, base_mw, added_mw, total_mw, base_normalized, total_normalized
    strategy: str
    n_vehicles: int
    daily_energy_added_mwh: float
    baseline_peak_mw: float
    baseline_peak_hour: int
    new_peak_mw: float
    new_peak_hour: int
    peak_increase_pct: float
    peak_hour_shifted: bool


def compute_added_load(
    n_vehicles: int,
    *,
    avg_annual_kwh_per_vehicle: float,
    shape: dict[int, float],
) -> pl.DataFrame:
    """Energia total anual dos VEs, distribuída pelas 24h conforme `shape`,
    convertida em MW médios por hora (spec seção 15: potência = energia / tempo,
    nunca soma direta)."""
    daily_energy_mwh = n_vehicles * avg_annual_kwh_per_vehicle / 365 / 1000  # kWh -> MWh
    # shape[h] é a fração do dia consumida na hora h; energia_na_hora = daily_energy*shape[h];
    # potência média da hora (MW) = energia_na_hora (MWh) / 1h.
    rows = [{"hour": h, "added_mw": daily_energy_mwh * shape[h]} for h in range(24)]
    return pl.DataFrame(rows)


def apply_to_real_curve(
    real_curve_24h: pl.DataFrame,
    added_load: pl.DataFrame,
    *,
    strategy: str,
    n_vehicles: int,
    daily_energy_added_mwh: float,
) -> ChargingImpactResult:
    """Combina a curva REAL observada (`rj_average_24h.csv`) com a carga
    ESTIMADA de VEs, calculando o novo pico e o quanto ele aumenta."""
    merged = real_curve_24h.select(["hour", "avg_mw"]).rename({"avg_mw": "base_mw"}).join(
        added_load, on="hour", how="left"
    ).with_columns(
        (pl.col("base_mw") + pl.col("added_mw")).alias("total_mw")
    )
    base_mean = merged["base_mw"].mean()
    total_mean = merged["total_mw"].mean()
    merged = merged.with_columns(
        (pl.col("base_mw") / base_mean).alias("base_normalized"),
        (pl.col("total_mw") / total_mean).alias("total_normalized"),
    )

    baseline_peak_row = merged.sort("base_mw", descending=True).row(0, named=True)
    new_peak_row = merged.sort("total_mw", descending=True).row(0, named=True)

    peak_increase_pct = 100 * (new_peak_row["total_mw"] - baseline_peak_row["base_mw"]) / baseline_peak_row["base_mw"]

    return ChargingImpactResult(
        hourly=merged.sort("hour"),
        strategy=strategy,
        n_vehicles=n_vehicles,
        daily_energy_added_mwh=daily_energy_added_mwh,
        baseline_peak_mw=baseline_peak_row["base_mw"],
        baseline_peak_hour=baseline_peak_row["hour"],
        new_peak_mw=new_peak_row["total_mw"],
        new_peak_hour=new_peak_row["hour"],
        peak_increase_pct=peak_increase_pct,
        peak_hour_shifted=(baseline_peak_row["hour"] != new_peak_row["hour"]),
    )


def run_all_strategies(
    real_curve_24h: pl.DataFrame,
    n_vehicles: int,
    assumptions: dict | None = None,
) -> list[ChargingImpactResult]:
    cfg = assumptions or load_assumptions()
    cb = cfg["charging_behavior"]
    avg_kwh = cb["avg_annual_consumption_kwh_per_vehicle"]["central"]
    peak_hours = (17, 18, 19, 20)  # janela de pico Light-RJ / NREL, usada para o corte do smart charging
    reduction_pct = (cb["strategy_effects"]["smart_charging_peak_reduction_pct_low"] + cb["strategy_effects"]["smart_charging_peak_reduction_pct_high"]) / 2

    shapes = {
        "uncontrolled": uncontrolled_shape(),
        "smart": smart_charging_shape(uncontrolled_shape(), peak_hours, reduction_pct),
        "offpeak_shifted": offpeak_shifted_shape(),
    }

    results = []
    for strategy, shape in shapes.items():
        added = compute_added_load(n_vehicles, avg_annual_kwh_per_vehicle=avg_kwh, shape=shape)
        daily_energy = n_vehicles * avg_kwh / 365 / 1000
        result = apply_to_real_curve(
            real_curve_24h, added, strategy=strategy, n_vehicles=n_vehicles, daily_energy_added_mwh=daily_energy
        )
        results.append(result)
    return results
