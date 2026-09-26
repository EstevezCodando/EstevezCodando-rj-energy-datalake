"""Métricas de curva de carga (spec seção 30)."""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class LoadMetrics:
    average_load_mw: float
    peak_load_mw: float
    minimum_load_mw: float
    peak_hour: int
    minimum_hour: int
    peak_to_average_ratio: float
    daily_energy_mwh: float
    load_factor: float
    share_17_22: float
    share_18_21: float
    peak_3h_energy_share: float
    peak_valley_mw: float


def _share_for_hours(hourly: pl.DataFrame, hours: set[int], value_col: str) -> float:
    total = hourly[value_col].sum()
    if total == 0:
        return 0.0
    subset = hourly.filter(pl.col("hour").is_in(hours))[value_col].sum()
    return float(subset / total)


def compute_load_metrics(hourly_profile: pl.DataFrame, *, value_col: str = "avg_mw") -> LoadMetrics:
    """Recebe um perfil de 24 horas (uma linha por hora, 0-23) e calcula as
    métricas da spec seção 30. `value_col` é a potência média (MW) da hora.
    Energia diária é aproximada por soma(MW por hora * 1h), válido pois cada
    linha já representa a média/energia da hora.
    """
    if hourly_profile.height == 0:
        raise ValueError("hourly_profile vazio")

    sorted_df = hourly_profile.sort("hour")
    values = sorted_df[value_col]

    average = float(values.mean())
    peak = float(values.max())
    minimum = float(values.min())
    peak_hour = int(sorted_df.filter(pl.col(value_col) == peak)["hour"][0])
    minimum_hour = int(sorted_df.filter(pl.col(value_col) == minimum)["hour"][0])
    daily_energy = float(values.sum())  # 1h por linha
    load_factor = average / peak if peak else 0.0
    peak_to_average = peak / average if average else 0.0

    top3 = sorted_df.sort(value_col, descending=True).head(3)
    peak_3h_share = float(top3[value_col].sum() / daily_energy) if daily_energy else 0.0

    return LoadMetrics(
        average_load_mw=average,
        peak_load_mw=peak,
        minimum_load_mw=minimum,
        peak_hour=peak_hour,
        minimum_hour=minimum_hour,
        peak_to_average_ratio=peak_to_average,
        daily_energy_mwh=daily_energy,
        load_factor=load_factor,
        share_17_22=_share_for_hours(sorted_df, {17, 18, 19, 20, 21, 22}, value_col),
        share_18_21=_share_for_hours(sorted_df, {18, 19, 20, 21}, value_col),
        peak_3h_energy_share=peak_3h_share,
        peak_valley_mw=peak - minimum,
    )


def build_flexibility_candidates(hourly_profile: pl.DataFrame, *, value_col: str = "avg_mw") -> pl.DataFrame:
    """Tabela auxiliar para estudos de flexibilidade (spec seção 31). Apenas
    identifica janelas candidatas — não assume que toda carga acima da média
    seja de fato flexível."""
    sorted_df = hourly_profile.sort("hour")
    daily_mean = float(sorted_df[value_col].mean())
    p90 = float(sorted_df[value_col].quantile(0.90))

    return sorted_df.with_columns(
        pl.col(value_col).alias("baseline_mw"),
        (pl.col(value_col) - daily_mean).clip(lower_bound=0).alias("above_daily_mean_mw"),
        (pl.col(value_col) - p90).clip(lower_bound=0).alias("above_p90_mw"),
        pl.when(pl.col(value_col) > daily_mean)
        .then(pl.lit("candidate_peak_shift"))
        .otherwise(pl.lit("baseline"))
        .alias("potential_shift_window"),
    ).select(["hour", "baseline_mw", "above_daily_mean_mw", "above_p90_mw", "potential_shift_window"])
