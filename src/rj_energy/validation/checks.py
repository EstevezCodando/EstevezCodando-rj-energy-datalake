"""Critérios de qualidade (spec seção 23) e gate de promoção (spec seção 24).

Outliers são SINALIZADOS, nunca removidos automaticamente. Cada checagem
retorna um `ValidationOutcome`; checagens de severidade 'error' bloqueiam a
promoção para GOLD (ver `lifecycle.manifest.evaluate_gate`), 'warning' apenas
sinaliza.
"""

from __future__ import annotations

from datetime import timedelta

import polars as pl

from rj_energy.models import ValidationOutcome


def check_schema(df: pl.DataFrame, expected_columns: list[str]) -> ValidationOutcome:
    missing = [c for c in expected_columns if c not in df.columns]
    extra = [c for c in df.columns if c not in expected_columns]
    passed = not missing
    details = f"faltando={missing} extras={extra}" if (missing or extra) else "schema conforme o esperado"
    return ValidationOutcome(check_name="schema", passed=passed, severity="error", details=details)


def check_not_empty(df: pl.DataFrame, *, min_rows: int = 1) -> ValidationOutcome:
    passed = df.height >= min_rows
    return ValidationOutcome(
        check_name="not_empty", passed=passed, severity="error",
        details=f"{df.height} linhas (mínimo esperado: {min_rows})", rows_affected=df.height,
    )


def check_duplicates(df: pl.DataFrame, key_columns: list[str]) -> ValidationOutcome:
    if df.is_empty():
        return ValidationOutcome(check_name="duplicates", passed=True, severity="error", details="dataframe vazio")
    n_dupes = df.height - df.unique(subset=key_columns).height
    passed = n_dupes == 0
    return ValidationOutcome(
        check_name="duplicates", passed=passed, severity="error",
        details=f"{n_dupes} linhas duplicadas pela chave {key_columns}", rows_affected=n_dupes,
    )


def check_nulls(df: pl.DataFrame, required_columns: list[str]) -> ValidationOutcome:
    null_counts = {c: int(df[c].null_count()) for c in required_columns if c in df.columns}
    total_nulls = sum(null_counts.values())
    passed = total_nulls == 0
    return ValidationOutcome(
        check_name="unexpected_nulls", passed=passed, severity="error",
        details=f"nulos por coluna: {null_counts}", rows_affected=total_nulls,
    )


def check_negative_values(df: pl.DataFrame, value_column: str, *, allow_negative: bool = False) -> ValidationOutcome:
    if allow_negative or value_column not in df.columns:
        return ValidationOutcome(check_name="negative_values", passed=True, severity="warning", details="checagem não aplicável")
    n_negative = df.filter(pl.col(value_column) < 0).height
    passed = n_negative == 0
    return ValidationOutcome(
        check_name="negative_values", passed=passed, severity="warning",
        details=f"{n_negative} valores negativos inesperados em {value_column}", rows_affected=n_negative,
    )


def check_missing_hours(df: pl.DataFrame, date_col: str = "date", hour_col: str = "hour") -> ValidationOutcome:
    """Verifica se, para cada data presente, todas as 24 horas existem."""
    if df.is_empty():
        return ValidationOutcome(check_name="missing_hours", passed=True, severity="warning", details="dataframe vazio")
    per_date_counts = df.group_by(date_col).agg(pl.col(hour_col).n_unique().alias("n_hours"))
    incomplete = per_date_counts.filter(pl.col("n_hours") < 24)
    passed = incomplete.is_empty()
    return ValidationOutcome(
        check_name="missing_hours", passed=passed, severity="warning",
        details=f"{incomplete.height} datas com menos de 24 horas", rows_affected=incomplete.height,
    )


def check_coverage_regression(current_max_date, previous_max_date) -> ValidationOutcome:
    """Sinaliza se a nova versão cobre um período MENOR do que a versão anterior
    (regressão de cobertura temporal, spec seção 23-24)."""
    if previous_max_date is None or current_max_date is None:
        return ValidationOutcome(check_name="coverage_regression", passed=True, severity="error", details="sem baseline anterior para comparar")
    passed = current_max_date >= previous_max_date
    return ValidationOutcome(
        check_name="coverage_regression", passed=passed, severity="error",
        details=f"cobertura atual até {current_max_date}, anterior até {previous_max_date}",
    )


def check_row_count_anomaly(current_row_count: int, historical_row_counts: list[int], *, z_threshold: float = 3.0) -> ValidationOutcome:
    """Compara a contagem de linhas atual com o histórico via z-score robusto
    (mediana + MAD). Sinaliza (severity=warning) anomalias sem bloquear sozinho."""
    if len(historical_row_counts) < 3:
        return ValidationOutcome(check_name="row_count_anomaly", passed=True, severity="warning", details="histórico insuficiente para comparação")

    counts = pl.Series(historical_row_counts)
    median = counts.median()
    mad = (counts - median).abs().median()
    if mad == 0:
        passed = current_row_count == median
        z = float("inf") if not passed else 0.0
    else:
        z = 0.6745 * (current_row_count - median) / mad
        passed = abs(z) <= z_threshold
    return ValidationOutcome(
        check_name="row_count_anomaly", passed=passed, severity="warning",
        details=f"row_count={current_row_count}, mediana_historica={median}, z_robusto={z:.2f}",
    )


def check_energy_power_consistency(load_mw: float, energy_mwh: float, hours: float, *, tolerance_pct: float = 1.0) -> ValidationOutcome:
    """energy_mwh deve ser aproximadamente load_mw * hours (spec seção 23: 'inconsistência energia × potência')."""
    expected_energy = load_mw * hours
    if expected_energy == 0:
        passed = energy_mwh == 0
        error_pct = 0.0
    else:
        error_pct = 100 * abs(energy_mwh - expected_energy) / abs(expected_energy)
        passed = error_pct <= tolerance_pct
    return ValidationOutcome(
        check_name="energy_power_consistency", passed=passed, severity="warning",
        details=f"erro={error_pct:.2f}% (tolerância={tolerance_pct}%)",
    )


def check_completeness_window(dates_present: list, expected_start, expected_end) -> ValidationOutcome:
    """Verifica se o período mais recente esperado está presente (spec seção 24, item 6)."""
    if not dates_present:
        return ValidationOutcome(check_name="completeness_window", passed=False, severity="error", details="nenhuma data presente")
    max_date = max(dates_present)
    passed = max_date >= expected_end - timedelta(days=1)
    return ValidationOutcome(
        check_name="completeness_window", passed=passed, severity="error",
        details=f"data mais recente presente={max_date}, esperado até~{expected_end}",
    )
