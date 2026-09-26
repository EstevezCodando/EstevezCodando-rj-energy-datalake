"""Tratamento ANEEL CTR — Curva de Carga, consumidor-tipo (spec seção 16).

Nunca hardcoda categorias (SigCcs, NomSubGrupoTarifario, DscDemandante,
DscTipoDia) antes de inspecionar os valores realmente presentes no arquivo —
`distinct_category_values()` deve ser chamada e registrada em log antes de
qualquer filtro.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

CATEGORY_COLUMNS = ["SigCcs", "NomSubGrupoTarifario", "DscDemandante", "DscTipoDia"]

_CSV_SEPARATORS = (";", ",", "\t")
_CSV_ENCODINGS = ("utf-8", "latin-1", "cp1252")


def load_consumidor_tipo(path: Path) -> pl.DataFrame:
    """Carrega o arquivo consumidor-tipo (Parquet ou CSV), detectando
    automaticamente separador/encoding no caso de CSV (spec seção 16)."""
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        df = pl.read_parquet(path)
    else:
        df = _read_csv_autodetect(path)

    return df.with_columns(
        pl.col("HorInicial").cast(pl.Utf8, strict=False),
        pl.col("HorFinal").cast(pl.Utf8, strict=False),
        _to_float_column("VlrDmd"),
    )


def _to_float_column(name: str) -> pl.Expr:
    # Detecta separador decimal vírgula vs ponto antes do cast.
    return (
        pl.col(name)
        .cast(pl.Utf8, strict=False)
        .str.replace(",", ".", literal=True)
        .cast(pl.Float64, strict=False)
        .alias(name)
    )


def _read_csv_autodetect(path: Path) -> pl.DataFrame:
    last_error: Exception | None = None
    for encoding in _CSV_ENCODINGS:
        for sep in _CSV_SEPARATORS:
            try:
                df = pl.read_csv(path, separator=sep, encoding=encoding, infer_schema_length=1000, truncate_ragged_lines=True)
                if df.width > 1:
                    return df
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue
    raise ValueError(f"Não foi possível detectar separador/encoding de {path}") from last_error


def distinct_category_values(df: pl.DataFrame) -> dict[str, list[str]]:
    """Retorna os valores únicos das colunas categóricas antes de qualquer filtro —
    deve ser inspecionado/logado antes de assumir categorias (spec seção 16)."""
    return {col: sorted(df[col].drop_nulls().unique().to_list()) for col in CATEGORY_COLUMNS if col in df.columns}


def _hour_from_hor_inicial(hor_inicial: str) -> int:
    # HorInicial normalmente vem como "HH:MM" ou "HH:MM:SS".
    return int(hor_inicial.split(":")[0])


def build_curve_stats(df: pl.DataFrame, *, distributor_col: str = "SigCcs") -> pl.DataFrame:
    """Constrói curvas por distribuidora/classe/subgrupo/tipo de dia/hora, com
    média, mediana, percentis, desvio-padrão e contagem (spec seção 16)."""
    working = df.with_columns(
        pl.col("HorInicial").map_elements(_hour_from_hor_inicial, return_dtype=pl.Int8).alias("hour"),
    )
    group_cols = [distributor_col, "DscDemandante", "NomSubGrupoTarifario", "DscTipoDia", "hour"]

    stats = working.group_by(group_cols).agg(
        pl.col("VlrDmd").mean().alias("mean_mw"),
        pl.col("VlrDmd").median().alias("median_mw"),
        pl.col("VlrDmd").quantile(0.05).alias("p05_mw"),
        pl.col("VlrDmd").quantile(0.25).alias("p25_mw"),
        pl.col("VlrDmd").quantile(0.75).alias("p75_mw"),
        pl.col("VlrDmd").quantile(0.95).alias("p95_mw"),
        pl.col("VlrDmd").std().alias("std_mw"),
        pl.col("VlrDmd").count().alias("n_observations"),
    ).sort(group_cols)
    return stats


def normalize_curve(stats: pl.DataFrame, *, group_cols: list[str] | None = None) -> pl.DataFrame:
    """Adiciona `normalized_load = mean_mw / média_diária_do_grupo`. A média
    diária da curva normalizada deve ficar aproximadamente 1 (spec seção 16)."""
    group_cols = group_cols or ["SigCcs", "DscDemandante", "NomSubGrupoTarifario", "DscTipoDia"]
    daily_mean = stats.group_by(group_cols).agg(pl.col("mean_mw").mean().alias("daily_mean_mw"))
    joined = stats.join(daily_mean, on=group_cols, how="left")
    return joined.with_columns((pl.col("mean_mw") / pl.col("daily_mean_mw")).alias("normalized_load"))
