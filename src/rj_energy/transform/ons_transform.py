"""Tratamento ONS — Carga de Energia Verificada (spec seção 15).

`val_cargaglobal` é publicado em MWmed por intervalo de 30 minutos. A conversão
para potência/energia horária segue exatamente as fórmulas da especificação:

    load_hourly_mw    = mean(duas leituras de 30 min)
    energy_interval_mwh = load_mw * 0.5
    energy_hourly_mwh  = sum(duas energy_interval_mwh)

Nunca soma MW diretamente para representar MW horário.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from rj_energy.models import GeographicPrecision, GeographicScope, ObservationType
from rj_energy.transform.temporal import add_temporal_columns
from rj_energy.utils.logging import get_logger, log_event

logger = get_logger(__name__)

RAW_FIELDS = [
    "cod_areacarga", "dat_referencia", "din_referenciautc", "din_atualizacao", "val_cargaglobal",
    "val_cargaglobalsmmgd", "val_cargammgd", "val_cargaglobalcons", "val_consistencia",
    "val_cargasupervisionada", "val_carganaosupervisionada",
]
# Nota: o dicionário de dados da spec original lista `val_cargaglobalsmmg`, mas a
# API em produção (`apicarga.ons.org.br`) retorna `val_cargaglobalsmmgd` (com "d"
# no final) e um campo adicional `din_atualizacao` — confirmado por observação
# direta da API real. `val_consistencia` também retorna como código numérico
# (ex.: 0), não como string descritiva.


def parse_raw_json(path: Path) -> pl.DataFrame:
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    records = payload if isinstance(payload, list) else payload.get("data", payload.get("result", []))
    if not records:
        return pl.DataFrame(schema={f: pl.Utf8 for f in RAW_FIELDS})
    return pl.DataFrame(records)


def to_silver_30min(raw_df: pl.DataFrame, *, source_resource_id: str, retrieved_at: str) -> pl.DataFrame:
    """Converte o JSON bruto (30 min) em uma tabela SILVER tipada, com colunas
    temporais padronizadas e proveniência mínima. Preserva os dados originais
    de 30 minutos (spec: 'preservar os dados originais de 30 minutos')."""
    if raw_df.is_empty():
        return raw_df

    df = raw_df.with_columns(
        # A API real retorna ISO 8601 com offset explícito (ex.: "...Z"); fixamos
        # time_zone="UTC" para que o parsing não dependa de heurística implícita.
        pl.col("din_referenciautc").str.to_datetime(strict=False, time_zone="UTC"),
        pl.col("val_cargaglobal").cast(pl.Float64, strict=False),
        pl.col("val_cargaglobalcons").cast(pl.Float64, strict=False) if "val_cargaglobalcons" in raw_df.columns else pl.lit(None).alias("val_cargaglobalcons"),
        pl.col("val_consistencia").cast(pl.Utf8, strict=False) if "val_consistencia" in raw_df.columns else pl.lit(None).alias("val_consistencia"),
    )

    # Observado em produção: os intervalos de 30min mais recentes (ainda não
    # consolidados pelo ONS, tipicamente os últimos 1-2 registros de uma janela
    # que inclui "agora") vêm com val_cargaglobal=0 como placeholder, não como
    # uma medição real — a carga de uma área geoelétrica inteira nunca é
    # fisicamente zero. Tratamos esse valor como ausente (null) em vez de
    # incluí-lo como leitura válida, para nunca inventar/contaminar a média
    # horária com um zero espúrio (spec: "nunca inventar valores ausentes" e
    # "não tratar automaticamente o arquivo mais recente como o correto").
    # A hora correspondente fica marcada como `incomplete_hour` em
    # `aggregate_hourly` em vez de silenciosamente errada.
    n_zero_placeholders = df.filter(pl.col("val_cargaglobal") == 0).height
    if n_zero_placeholders:
        log_event(
            logger, "ons_zero_placeholder_nulled",
            "Valores val_cargaglobal=0 (placeholder de intervalo ainda não consolidado) tratados como ausentes",
            resource_id=source_resource_id, count=n_zero_placeholders,
        )
    df = df.with_columns(
        pl.when(pl.col("val_cargaglobal") == 0).then(None).otherwise(pl.col("val_cargaglobal")).alias("val_cargaglobal")
    )

    df = add_temporal_columns(df, "din_referenciautc", source_is_utc=True)

    return df.with_columns(
        pl.lit("ons").alias("source"),
        pl.lit("carga_verificada").alias("dataset"),
        pl.lit(source_resource_id).alias("resource_id"),
        pl.lit(retrieved_at).alias("retrieved_at"),
        pl.lit(GeographicScope.ONS_LOAD_AREA.value).alias("geographic_scope"),
        pl.lit(GeographicPrecision.APPROXIMATE.value).alias("geographic_precision"),  # área ONS RJ ≠ limite estadual exato
        pl.lit(ObservationType.OBSERVED.value).alias("observation_type"),
        pl.col("val_cargaglobal").alias("load_mw"),
    )


def aggregate_hourly(df_30min: pl.DataFrame) -> pl.DataFrame:
    """Agrega os dois intervalos de 30 min de cada hora em uma linha horária
    (spec seção 15). Só agrega horas com as DUAS leituras presentes; horas
    incompletas ficam com `quality_flag='incomplete_hour'` e não entram no
    cálculo de energia (nunca inventa valores ausentes)."""
    if df_30min.is_empty():
        return df_30min

    grouped = (
        df_30min.group_by(["date", "year", "month", "day", "hour", "day_type", "source", "dataset", "geographic_scope", "geographic_precision"])
        .agg(
            pl.col("load_mw").mean().alias("load_hourly_mw"),
            pl.col("load_mw").count().alias("n_intervals"),
            (pl.col("load_mw") * 0.5).sum().alias("energy_hourly_mwh"),
        )
        .with_columns(
            pl.when(pl.col("n_intervals") >= 2)
            .then(pl.lit("ok"))
            .otherwise(pl.lit("incomplete_hour"))
            .alias("quality_flag"),
            pl.lit(ObservationType.AGGREGATED.value).alias("observation_type"),
        )
        .sort(["date", "hour"])
    )
    return grouped
