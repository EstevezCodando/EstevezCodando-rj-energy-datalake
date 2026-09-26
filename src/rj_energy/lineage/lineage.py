"""Tabela de lineage entre produtos GOLD e as versões de fontes utilizadas
(spec seção 11): `gold_dataset_lineage`."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import polars as pl

LINEAGE_SCHEMA: dict[str, pl.PolarsDataType] = {
    "gold_dataset": pl.Utf8,
    "gold_version": pl.Utf8,
    "source": pl.Utf8,
    "resource_id": pl.Utf8,
    "source_hash": pl.Utf8,
    "reference_period": pl.Utf8,
    "pipeline_version": pl.Utf8,
    "created_at": pl.Utf8,
}


def empty_lineage() -> pl.DataFrame:
    return pl.DataFrame(schema=LINEAGE_SCHEMA)


def load_lineage(path: Path) -> pl.DataFrame:
    return pl.read_parquet(path) if path.exists() else empty_lineage()


def save_lineage(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)


def record_lineage(
    lineage_df: pl.DataFrame,
    *,
    gold_dataset: str,
    gold_version: str,
    source_versions: list[dict],
    pipeline_version: str,
) -> pl.DataFrame:
    """`source_versions`: lista de dicts com chaves source, resource_id, source_hash, reference_period."""
    now = datetime.now(UTC).isoformat()
    rows = [
        {
            "gold_dataset": gold_dataset,
            "gold_version": gold_version,
            "source": sv["source"],
            "resource_id": sv["resource_id"],
            "source_hash": sv.get("source_hash"),
            "reference_period": sv.get("reference_period"),
            "pipeline_version": pipeline_version,
            "created_at": now,
        }
        for sv in source_versions
    ]
    new_rows = pl.DataFrame(rows, schema=LINEAGE_SCHEMA)
    return new_rows if lineage_df.is_empty() else pl.concat([lineage_df, new_rows], how="vertical")
