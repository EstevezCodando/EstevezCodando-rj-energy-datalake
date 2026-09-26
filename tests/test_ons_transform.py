from rj_energy.transform.ons_transform import (
    aggregate_hourly,
    parse_raw_json,
    to_silver_30min,
)


def test_parse_and_aggregate_hourly(fixtures_dir):
    raw_path = fixtures_dir / "ons_carga_verificada_sample.json"
    raw_df = parse_raw_json(raw_path)
    assert raw_df.height == 5

    silver = to_silver_30min(raw_df, source_resource_id="ons-RJ-2026-06-02", retrieved_at="2026-06-02T20:00:00")
    assert silver.height == 5
    # 13:00 UTC -> 10:00 local (America/Sao_Paulo, UTC-3 sem DST desde 2019).
    assert set(silver["hour"].to_list()) == {10, 11, 12}

    hourly = aggregate_hourly(silver)
    # Hora 10 (13:00-13:30 UTC) tem 2 leituras completas: 1000.0 e 1010.0.
    row_10 = hourly.filter(hourly["hour"] == 10).row(0, named=True)
    assert row_10["load_hourly_mw"] == 1005.0
    assert row_10["energy_hourly_mwh"] == 1000.0 * 0.5 + 1010.0 * 0.5
    assert row_10["quality_flag"] == "ok"

    # Hora 12 (15:00 UTC) só tem 1 leitura -> hora incompleta.
    row_12 = hourly.filter(hourly["hour"] == 12).row(0, named=True)
    assert row_12["quality_flag"] == "incomplete_hour"
    assert row_12["n_intervals"] == 1


def test_energy_never_summed_as_raw_mw(fixtures_dir):
    """Garante que load_hourly_mw é uma MÉDIA, não uma SOMA das leituras de 30 min
    (spec seção 15: 'nunca somar MW diretamente para representar MW horário')."""
    raw_df = parse_raw_json(fixtures_dir / "ons_carga_verificada_sample.json")
    silver = to_silver_30min(raw_df, source_resource_id="x", retrieved_at="2026-06-02T20:00:00")
    hourly = aggregate_hourly(silver)

    row_11 = hourly.filter(hourly["hour"] == 11).row(0, named=True)
    # Leituras da hora 11 (14:00 e 14:30 UTC): 1020.0 e 1030.0 -> média 1025.0, não soma 2050.0.
    assert row_11["load_hourly_mw"] == 1025.0


def test_trailing_zero_placeholder_is_treated_as_missing_not_as_a_reading(fixtures_dir):
    """Achado real em produção: os intervalos de 30min mais recentes (ainda não
    consolidados pelo ONS) vêm com val_cargaglobal=0 como placeholder, não como
    medição real (a carga de uma área geoelétrica inteira nunca é fisicamente
    zero). Isso NUNCA pode contaminar a média horária silenciosamente — a hora
    deve ficar `incomplete_hour`, usando apenas a leitura real disponível."""
    raw_df = parse_raw_json(fixtures_dir / "ons_trailing_zero_sample.json")
    silver = to_silver_30min(raw_df, source_resource_id="x", retrieved_at="2026-09-26T03:00:00")

    # O valor zero deve virar nulo na SILVER, não uma leitura válida de 0 MW.
    assert silver["load_mw"].null_count() == 1
    assert silver["load_mw"].drop_nulls().to_list() == [6255.6074]

    hourly = aggregate_hourly(silver)
    row = hourly.row(0, named=True)
    assert row["quality_flag"] == "incomplete_hour"
    assert row["n_intervals"] == 1
    # A média usa só a leitura real (6255.6074), nunca é contaminada pelo zero.
    assert row["load_hourly_mw"] == 6255.6074
