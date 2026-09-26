"""Tratamento EPE — Consumo Mensal de Energia Elétrica (spec seção 18).

Nunca presume a grafia de `UF` antes de inspecionar os valores únicos
efetivamente presentes no arquivo (pode ser "RJ", "Rio de Janeiro", etc.).
"""

from __future__ import annotations

import calendar
from pathlib import Path

import polars as pl

EXPECTED_COLUMNS = ["Data", "DataExcel", "UF", "Regiao", "Sistema", "Classe", "TipoConsumidor", "Consumo", "Consumidores", "DataVersao"]


def load_consumo_mensal(path: Path, *, sheet_name: str | None = None) -> pl.DataFrame:
    return pl.read_excel(path, sheet_name=sheet_name) if sheet_name else pl.read_excel(path)


def distinct_uf_values(df: pl.DataFrame) -> list[str]:
    return sorted(df["UF"].drop_nulls().unique().to_list()) if "UF" in df.columns else []


def resolve_rj_label(distinct_ufs: list[str]) -> str | None:
    """Encontra a grafia usada para o Rio de Janeiro entre os valores únicos de UF,
    sem presumir 'RJ' de antemão (spec seção 18)."""
    for candidate in distinct_ufs:
        normalized = candidate.strip().lower()
        if normalized in {"rj", "rio de janeiro"}:
            return candidate
    return None


def filter_rj(df: pl.DataFrame) -> pl.DataFrame:
    ufs = distinct_uf_values(df)
    rj_label = resolve_rj_label(ufs)
    if rj_label is None:
        raise ValueError(f"Não foi possível localizar o rótulo do RJ entre os valores de UF encontrados: {ufs}")
    return df.filter(pl.col("UF") == rj_label)


def average_monthly_power_mw(monthly_energy_mwh: float, year: int, month: int) -> float:
    """average_monthly_power_mw = monthly_energy_mwh / hours_in_month (spec seção 18)."""
    hours_in_month = calendar.monthrange(year, month)[1] * 24
    return monthly_energy_mwh / hours_in_month
