import polars as pl
import pytest
from charging_impact import (
    apply_to_real_curve,
    compute_added_load,
    offpeak_shifted_shape,
    smart_charging_shape,
    uncontrolled_shape,
)


def _flat_real_curve(mw: float = 1000.0) -> pl.DataFrame:
    return pl.DataFrame({"hour": list(range(24)), "avg_mw": [mw] * 24})


def test_shapes_sum_to_one():
    for shape in (uncontrolled_shape(), offpeak_shifted_shape()):
        assert abs(sum(shape.values()) - 1.0) < 1e-9


def test_uncontrolled_shape_peaks_at_18h():
    shape = uncontrolled_shape()
    peak_hour = max(shape, key=shape.get)
    assert peak_hour == 18


def test_offpeak_shifted_shape_confined_to_window():
    shape = offpeak_shifted_shape(0, 6)
    for hour, weight in shape.items():
        if 0 <= hour < 6:
            assert weight > 0
        else:
            assert weight == 0


def test_smart_charging_preserves_total_energy():
    base = uncontrolled_shape()
    smart = smart_charging_shape(base, peak_hours=(17, 18, 19, 20), reduction_pct=50)
    assert abs(sum(smart.values()) - sum(base.values())) < 1e-9


def test_smart_charging_reduces_peak_hours():
    base = uncontrolled_shape()
    smart = smart_charging_shape(base, peak_hours=(17, 18, 19, 20), reduction_pct=50)
    for h in (17, 18, 19, 20):
        assert smart[h] < base[h]


def test_compute_added_load_energy_conservation():
    """A energia total adicionada ao longo do dia deve bater com
    n_veiculos * kwh_por_veiculo / 365, dentro de erro de arredondamento."""
    n_vehicles = 100_000
    kwh_per_vehicle = 2000.0
    shape = uncontrolled_shape()
    added = compute_added_load(n_vehicles, avg_annual_kwh_per_vehicle=kwh_per_vehicle, shape=shape)

    expected_daily_mwh = n_vehicles * kwh_per_vehicle / 365 / 1000
    actual_daily_mwh = added["added_mw"].sum()  # soma de MW médios por hora (1h cada) = MWh do dia
    assert abs(actual_daily_mwh - expected_daily_mwh) < 1e-6


def test_apply_to_real_curve_uncontrolled_increases_peak():
    real_curve = _flat_real_curve(1000.0)
    added = compute_added_load(500_000, avg_annual_kwh_per_vehicle=2000.0, shape=uncontrolled_shape())
    result = apply_to_real_curve(
        real_curve, added, strategy="uncontrolled", n_vehicles=500_000, daily_energy_added_mwh=added["added_mw"].sum()
    )
    assert result.new_peak_mw > result.baseline_peak_mw
    assert result.peak_increase_pct > 0


def test_apply_to_real_curve_offpeak_shifted_does_not_touch_evening_peak():
    """Uma curva base achatada + carga toda deslocada para 0h-6h nunca deve
    mudar o pico se a base já tem seu próprio pico fora dessa janela."""
    hours = list(range(24))
    base_mw = [1000.0] * 17 + [2000.0] + [1000.0] * 6  # pico artificial às 17h
    real_curve = pl.DataFrame({"hour": hours, "avg_mw": base_mw})

    added = compute_added_load(1_000_000, avg_annual_kwh_per_vehicle=2000.0, shape=offpeak_shifted_shape())
    result = apply_to_real_curve(
        real_curve, added, strategy="offpeak_shifted", n_vehicles=1_000_000, daily_energy_added_mwh=added["added_mw"].sum()
    )
    assert result.new_peak_hour == 17
    assert result.new_peak_mw == pytest.approx(2000.0)
