from datetime import date, datetime
from zoneinfo import ZoneInfo

from rj_energy.transform.temporal import (
    classify_day_type,
    count_day_types_in_month,
    to_temporal_fields,
)


def test_classify_day_type_national_holiday():
    # 25/12 (Natal) é feriado nacional em qualquer ano.
    assert classify_day_type(date(2026, 12, 25)) == "holiday"


def test_classify_day_type_weekday_saturday_sunday():
    # 2026-06-01 é uma segunda-feira (verificado no calendário gregoriano).
    assert classify_day_type(date(2026, 6, 1)) == "weekday"
    assert classify_day_type(date(2026, 6, 6)) == "saturday"
    assert classify_day_type(date(2026, 6, 7)) == "sunday"


def test_holiday_takes_precedence_over_weekday():
    # 07/09 (Independência) cai numa segunda-feira em 2026; deve ser 'holiday', não 'weekday'.
    d = date(2026, 9, 7)
    assert d.weekday() == 0  # segunda-feira
    assert classify_day_type(d) == "holiday"


def test_to_temporal_fields_utc_to_local_conversion():
    # 2026-06-02T13:00:00 UTC -> America/Sao_Paulo (UTC-3, sem horário de verão desde 2019) = 10:00 local.
    dt_utc = datetime(2026, 6, 2, 13, 0, 0, tzinfo=ZoneInfo("UTC"))
    fields = to_temporal_fields(dt_utc, source_is_utc=True)
    assert fields.hour == 10
    assert fields.timestamp_local.hour == 10
    assert fields.timestamp_utc.hour == 13
    assert fields.day_type == "weekday"


def test_to_temporal_fields_handles_historical_dst():
    # 2015-10-20 estava dentro do horário de verão brasileiro (UTC-2 no RJ).
    # zoneinfo deve aplicar o offset histórico correto automaticamente.
    dt_utc = datetime(2015, 10, 20, 13, 0, 0, tzinfo=ZoneInfo("UTC"))
    fields = to_temporal_fields(dt_utc, source_is_utc=True)
    assert fields.hour == 11  # UTC-2 durante o horário de verão de 2015


def test_count_day_types_in_month_sums_to_days_in_month():
    counts = count_day_types_in_month(2026, 6)
    assert sum(counts.values()) == 30
