from datetime import date

import polars as pl

from rj_energy.validation.checks import (
    check_coverage_regression,
    check_duplicates,
    check_energy_power_consistency,
    check_negative_values,
    check_nulls,
    check_row_count_anomaly,
    check_schema,
)


def test_check_schema_detects_missing_columns():
    df = pl.DataFrame({"a": [1], "b": [2]})
    outcome = check_schema(df, ["a", "b", "c"])
    assert not outcome.passed
    assert "c" in outcome.details


def test_check_duplicates():
    df = pl.DataFrame({"key": [1, 1, 2], "value": [10, 10, 20]})
    outcome = check_duplicates(df, ["key"])
    assert not outcome.passed
    assert outcome.rows_affected == 1


def test_check_nulls():
    df = pl.DataFrame({"a": [1, None, 3]})
    outcome = check_nulls(df, ["a"])
    assert not outcome.passed
    assert outcome.rows_affected == 1


def test_check_negative_values():
    df = pl.DataFrame({"load_mw": [10.0, -5.0, 3.0]})
    outcome = check_negative_values(df, "load_mw")
    assert not outcome.passed
    assert outcome.rows_affected == 1


def test_check_coverage_regression_flags_shrinking_window():
    outcome = check_coverage_regression(date(2026, 5, 1), date(2026, 6, 1))
    assert not outcome.passed


def test_check_coverage_regression_passes_when_extended():
    outcome = check_coverage_regression(date(2026, 7, 1), date(2026, 6, 1))
    assert outcome.passed


def test_check_row_count_anomaly_flags_outlier():
    outcome = check_row_count_anomaly(10, [1000, 998, 1002, 1001, 999])
    assert not outcome.passed


def test_check_row_count_anomaly_passes_within_range():
    outcome = check_row_count_anomaly(1000, [995, 998, 1002, 1001, 999])
    assert outcome.passed


def test_check_energy_power_consistency():
    outcome = check_energy_power_consistency(load_mw=100.0, energy_mwh=100.0, hours=1.0)
    assert outcome.passed

    bad = check_energy_power_consistency(load_mw=100.0, energy_mwh=50.0, hours=1.0)
    assert not bad.passed
