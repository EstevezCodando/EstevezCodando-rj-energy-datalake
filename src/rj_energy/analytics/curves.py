"""Construção da curva estadual (spec seção 22).

Duas famílias distintas e nunca misturadas silenciosamente:

  A — curvas OBSERVADAS: vêm diretamente de ONS/CCEE (mensuração real).
  B — curvas ESTIMADAS para o estado: forma normalizada (ANEEL CTR) calibrada
      pela energia mensal da EPE.

    f_h            = P_h / mean(P_0..P_23)
    P_month_avg    = E_month_MWh / hours_in_month
    P_RJ_h         = f_h * P_month_avg

Ponderado pelo número real de dias úteis/sábados/domingos/feriados no mês.
Meta pós-calibração: abs(error_pct) < 1%.
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class CalibrationResult:
    curve: pl.DataFrame  # colunas: day_type, hour, normalized_load (f_h), estimated_load_mw
    estimated_energy_mwh: float
    reference_energy_mwh: float
    error_pct: float


def calibrate_state_curve(
    shape_by_day_type: dict[str, pl.DataFrame],
    *,
    day_type_counts: dict[str, int],
    reference_energy_mwh: float,
    normalized_col: str = "normalized_load",
    hour_col: str = "hour",
) -> CalibrationResult:
    """`shape_by_day_type`: mapa day_type -> DataFrame com colunas [hour, normalized_load],
    onde normalized_load é a curva já normalizada (média diária ≈ 1) obtida do
    ANEEL CTR (spec seção 16). `day_type_counts`: nº real de dias de cada tipo
    no mês (spec: 'ponderar pelo número real de dias')."""

    total_hours = sum(day_type_counts.get(dt, 0) * 24 for dt in shape_by_day_type)
    if total_hours == 0:
        raise ValueError("day_type_counts não cobre nenhum dos day_types fornecidos em shape_by_day_type")

    p_month_avg = reference_energy_mwh / total_hours

    rows = []
    for day_type, shape_df in shape_by_day_type.items():
        n_days = day_type_counts.get(day_type, 0)
        for row in shape_df.iter_rows(named=True):
            f_h = row[normalized_col]
            p_rj_h = f_h * p_month_avg
            rows.append({
                "day_type": day_type,
                "hour": row[hour_col],
                "normalized_load": f_h,
                "estimated_load_mw": p_rj_h,
                "n_days_in_month": n_days,
            })

    curve = pl.DataFrame(rows)

    estimated_energy = float(
        curve.with_columns((pl.col("estimated_load_mw") * pl.col("n_days_in_month") * 1.0).alias("energy_contribution_mwh"))[
            "energy_contribution_mwh"
        ].sum()
    )
    error_pct = 100 * (estimated_energy - reference_energy_mwh) / reference_energy_mwh if reference_energy_mwh else 0.0

    return CalibrationResult(
        curve=curve,
        estimated_energy_mwh=estimated_energy,
        reference_energy_mwh=reference_energy_mwh,
        error_pct=error_pct,
    )
