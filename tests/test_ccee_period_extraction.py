from rj_energy.crawlers.ccee import extract_reference_period


def test_extract_reference_period_yyyy_mm():
    assert extract_reference_period("consumo_horario_202607.csv.gz") == "2026-07"


def test_extract_reference_period_month_name_pt():
    assert extract_reference_period("Consumo Horário - Julho de 2026") == "2026-07"
    assert extract_reference_period("consumo-marco-2026") == "2026-03"


def test_extract_reference_period_returns_none_when_unresolvable():
    assert extract_reference_period("arquivo-sem-data") is None
