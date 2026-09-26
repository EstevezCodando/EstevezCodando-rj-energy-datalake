"""Normalização temporal (spec seção 14).

Usa o banco de fusos horários do sistema (via `zoneinfo`) para converter entre
UTC e America/Sao_Paulo, o que trata corretamente os deslocamentos históricos
de horário de verão brasileiro (abolido em 2019) — nunca subtraindo/somando um
offset fixo de 3 horas.

O calendário de feriados usa a biblioteca `holidays`, com feriados nacionais e
estaduais do Rio de Janeiro.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

import holidays
import polars as pl

TZ_LOCAL = ZoneInfo("America/Sao_Paulo")
TZ_UTC = ZoneInfo("UTC")


@lru_cache(maxsize=1)
def _rj_holiday_calendar() -> holidays.HolidayBase:
    # years=None -> a biblioteca calcula sob demanda para qualquer ano consultado.
    return holidays.country_holidays("BR", subdiv="RJ")


def classify_day_type(local_date: date) -> str:
    """Classifica em 'holiday' > 'saturday' > 'sunday' > 'weekday' (feriado tem precedência)."""
    if local_date in _rj_holiday_calendar():
        return "holiday"
    weekday = local_date.weekday()  # 0=segunda ... 6=domingo
    if weekday == 5:
        return "saturday"
    if weekday == 6:
        return "sunday"
    return "weekday"


@dataclass(frozen=True)
class TemporalFields:
    timestamp_local: datetime
    timestamp_utc: datetime
    date: date
    year: int
    month: int
    day: int
    hour: int
    minute: int
    weekday: int
    day_type: str


def to_temporal_fields(dt: datetime, *, source_is_utc: bool) -> TemporalFields:
    """Recebe um datetime (aware ou naive) e produz os campos temporais padronizados.

    `source_is_utc=True` quando o valor de origem já é UTC (ex.: `din_referenciautc`
    do ONS); caso contrário assume-se horário local de origem (America/Sao_Paulo).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ_UTC if source_is_utc else TZ_LOCAL)
    elif source_is_utc:
        dt = dt.astimezone(TZ_UTC)

    dt_utc = dt.astimezone(TZ_UTC)
    dt_local = dt.astimezone(TZ_LOCAL)

    return TemporalFields(
        timestamp_local=dt_local,
        timestamp_utc=dt_utc,
        date=dt_local.date(),
        year=dt_local.year,
        month=dt_local.month,
        day=dt_local.day,
        hour=dt_local.hour,
        minute=dt_local.minute,
        weekday=dt_local.weekday(),
        day_type=classify_day_type(dt_local.date()),
    )


def add_temporal_columns(df: pl.DataFrame, timestamp_col: str, *, source_is_utc: bool) -> pl.DataFrame:
    """Adiciona as colunas temporais padronizadas (spec seção 14) a um DataFrame Polars,
    a partir de uma coluna de timestamp existente.
    """
    fields = [to_temporal_fields(ts, source_is_utc=source_is_utc) for ts in df[timestamp_col].to_list()]
    return df.with_columns(
        pl.Series("timestamp_local", [f.timestamp_local for f in fields]),
        pl.Series("timestamp_utc", [f.timestamp_utc for f in fields]),
        pl.Series("date", [f.date for f in fields]),
        pl.Series("year", [f.year for f in fields], dtype=pl.Int32),
        pl.Series("month", [f.month for f in fields], dtype=pl.Int8),
        pl.Series("day", [f.day for f in fields], dtype=pl.Int8),
        pl.Series("hour", [f.hour for f in fields], dtype=pl.Int8),
        pl.Series("minute", [f.minute for f in fields], dtype=pl.Int8),
        pl.Series("weekday", [f.weekday for f in fields], dtype=pl.Int8),
        pl.Series("day_type", [f.day_type for f in fields]),
    )


def count_day_types_in_month(year: int, month: int) -> dict[str, int]:
    """Conta dias úteis/sábados/domingos/feriados em um mês (usado na ponderação
    da calibração da curva estadual, spec seção 22)."""
    import calendar as _calendar

    counts = {"weekday": 0, "saturday": 0, "sunday": 0, "holiday": 0}
    days_in_month = _calendar.monthrange(year, month)[1]
    for day in range(1, days_in_month + 1):
        counts[classify_day_type(date(year, month, day))] += 1
    return counts
