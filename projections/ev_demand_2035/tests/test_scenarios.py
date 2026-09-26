from scenarios import (
    load_assumptions,
    national_light_ev_scenarios,
    pde2035_all_modes_reference,
    rj_ev_scenarios,
    rj_historical_cagr,
    rj_weight_bounds,
)


def test_national_scenarios_reproduce_epe_anchors_exactly():
    """O cenário conservador deve reproduzir EXATAMENTE os 3 pontos publicados
    pela EPE (2026=0.7, 2030=1.8, 2035=3.4 TWh) — nenhuma interpolação nos
    próprios anos-âncora."""
    df = national_light_ev_scenarios()
    conservative = df.filter(df["scenario"] == "conservador")

    for year, expected in ((2026, 0.7), (2030, 1.8), (2035, 3.4)):
        row = conservative.filter(conservative["year"] == year).row(0, named=True)
        assert row["demand_light_ev_twh"] == expected
        assert row["value_type"] == "observed_anchor"


def test_national_scenarios_ordering_conservative_lt_intermediate_lt_accelerated():
    df = national_light_ev_scenarios()
    for year in df["year"].unique().to_list():
        by_scenario = {
            r["scenario"]: r["demand_light_ev_twh"]
            for r in df.filter(df["year"] == year).iter_rows(named=True)
        }
        assert by_scenario["conservador"] <= by_scenario["intermediario"] <= by_scenario["acelerado"]


def test_accelerated_matches_turbo_ratio_at_anchor_year():
    """No ano em que a EPE publicou o cenário turbo (2034), o acelerado deve
    valer exatamente o número turbo publicado (5.0 TWh) — não uma aproximação."""
    df = national_light_ev_scenarios()
    row = df.filter((df["scenario"] == "acelerado") & (df["year"] == 2034)).row(0, named=True)
    assert abs(row["demand_light_ev_twh"] - 5.0) < 1e-9


def test_implied_fleet_grows_with_demand():
    df = national_light_ev_scenarios()
    conservative = df.filter(df["scenario"] == "conservador").sort("year")
    fleets = conservative["implied_bev_phev_fleet_units"].to_list()
    assert fleets == sorted(fleets)


def test_rj_weight_bounds_within_sane_range():
    low, high = rj_weight_bounds()
    assert 0 < low < high < 1
    assert low < 0.15  # RJ não deveria concentrar mais que ~15% da frota nacional


def test_rj_scenarios_scale_national_by_weight():
    assumptions = load_assumptions()
    national = national_light_ev_scenarios(assumptions)
    rj = rj_ev_scenarios(national, assumptions)

    nat_2035 = national.filter((national["scenario"] == "conservador") & (national["year"] == 2035)).row(0, named=True)
    rj_central_2035 = rj.filter(
        (rj["scenario"] == "conservador") & (rj["year"] == 2035) & (rj["rj_weight_case"] == "central")
    ).row(0, named=True)

    low, high = rj_weight_bounds(assumptions)
    ratio = rj_central_2035["demand_light_ev_twh"] / nat_2035["demand_light_ev_twh"]
    assert low <= ratio <= high


def test_rj_historical_cagr_is_positive_and_large():
    # Frota do RJ cresceu de 3.263 para 30.000+ em 4 anos — CAGR deve ser bem alto.
    cagr = rj_historical_cagr()
    assert cagr > 0.5


def test_pde2035_all_modes_reproduces_2035_anchor():
    """O ano-âncora 2025 fica fora do horizonte do modelo (que começa em 2026),
    mas 2035 é ambos ano-âncora E parte do horizonte — deve reproduzir 7.8 TWh
    exatamente."""
    df = pde2035_all_modes_reference()
    row_2035 = df.filter(df["year"] == 2035).row(0, named=True)
    assert abs(row_2035["demand_all_modes_twh"] - 7.8) < 1e-9
    assert row_2035["value_type"] == "observed_anchor"
