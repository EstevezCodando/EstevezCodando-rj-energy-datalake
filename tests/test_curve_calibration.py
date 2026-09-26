import polars as pl

from rj_energy.analytics.curves import calibrate_state_curve
from rj_energy.analytics.metrics import compute_load_metrics


def _flat_normalized_shape() -> pl.DataFrame:
    # Curva perfeitamente plana (normalized_load = 1 em todas as 24h) -> média diária = 1.
    return pl.DataFrame({"hour": list(range(24)), "normalized_load": [1.0] * 24})


def test_calibrate_state_curve_reproduces_reference_energy_within_tolerance():
    shape = {"weekday": _flat_normalized_shape(), "saturday": _flat_normalized_shape(), "sunday": _flat_normalized_shape()}
    day_type_counts = {"weekday": 22, "saturday": 4, "sunday": 4}
    reference_energy_mwh = 1_000_000.0

    result = calibrate_state_curve(shape, day_type_counts=day_type_counts, reference_energy_mwh=reference_energy_mwh)

    assert abs(result.error_pct) < 1.0
    assert result.estimated_energy_mwh > 0


def test_calibrate_state_curve_with_peaked_shape_still_matches_energy_total():
    # Curva com pico à noite, mas média diária ainda ~1 (soma normalizada = 24).
    # 21 horas em q + 3 horas de pico em 1.6, com q escolhido para que a média seja exatamente 1.0:
    # 21*q + 3*1.6 = 24  =>  q = 19.2 / 21
    hours = list(range(24))
    q = 19.2 / 21
    shape_values = [q] * 17 + [1.6, 1.6, 1.6] + [q] * 4
    shape_df = pl.DataFrame({"hour": hours, "normalized_load": shape_values})
    shape = {"weekday": shape_df}
    day_type_counts = {"weekday": 30}

    result = calibrate_state_curve(shape, day_type_counts=day_type_counts, reference_energy_mwh=500_000.0)
    assert abs(result.error_pct) < 1.0

    peak_hours = result.curve.filter(result.curve["normalized_load"] == 1.6)
    assert peak_hours.height == 3


def test_compute_load_metrics_basic():
    profile = pl.DataFrame({"hour": list(range(24)), "avg_mw": [100.0] * 17 + [200.0, 220.0, 210.0] + [100.0] * 4})
    metrics = compute_load_metrics(profile)

    assert metrics.peak_load_mw == 220.0
    assert metrics.peak_hour == 18
    assert metrics.minimum_load_mw == 100.0
    assert metrics.peak_to_average_ratio > 1.0
    assert 0 < metrics.load_factor <= 1.0
    assert metrics.peak_valley_mw == 120.0
