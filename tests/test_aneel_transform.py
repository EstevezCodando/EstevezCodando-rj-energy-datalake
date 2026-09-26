from rj_energy.transform.aneel_transform import (
    build_curve_stats,
    distinct_category_values,
    load_consumidor_tipo,
    normalize_curve,
)


def test_load_consumidor_tipo_autodetects_semicolon_and_decimal_comma(fixtures_dir):
    df = load_consumidor_tipo(fixtures_dir / "aneel_consumidor_tipo_sample.csv")
    assert df.height == 9
    assert df["VlrDmd"].dtype.is_numeric()
    row0 = df.row(0, named=True)
    assert row0["VlrDmd"] == 10.5


def test_distinct_category_values_before_filtering(fixtures_dir):
    df = load_consumidor_tipo(fixtures_dir / "aneel_consumidor_tipo_sample.csv")
    categories = distinct_category_values(df)
    assert set(categories["SigCcs"]) == {"LIGHT", "ENEL RJ"}
    assert set(categories["DscDemandante"]) == {"Residencial", "Industrial"}
    assert set(categories["DscTipoDia"]) == {"Dia Útil", "Sábado"}


def test_build_curve_stats_and_normalize(fixtures_dir):
    df = load_consumidor_tipo(fixtures_dir / "aneel_consumidor_tipo_sample.csv")
    stats = build_curve_stats(df)

    light_residencial = stats.filter(
        (stats["SigCcs"] == "LIGHT") & (stats["DscDemandante"] == "Residencial")
    ).sort("hour")
    assert light_residencial.height == 3
    assert light_residencial.row(0, named=True)["mean_mw"] == 10.5

    normalized = normalize_curve(stats)
    group = normalized.filter(
        (normalized["SigCcs"] == "LIGHT") & (normalized["DscDemandante"] == "Residencial")
    )
    # média (10.5+9.8+9.2)/3 = 9.8333...; normalized da hora 0 = 10.5/9.8333 > 1
    daily_mean = (10.5 + 9.8 + 9.2) / 3
    row0 = group.filter(group["hour"] == 0).row(0, named=True)
    assert abs(row0["normalized_load"] - (10.5 / daily_mean)) < 1e-9
