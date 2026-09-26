"""Manifest central (`metadata/manifest.parquet`) e máquina de ciclo de vida
(spec seções 4, 5, 13, 24).

Regra fundamental (spec seção 4): a camada GOLD usa `latest_valid_complete_version`,
nunca simplesmente `latest_downloaded_version`. Uma versão nova só é promovida
(`is_active_for_gold=True`) se passar pelo gate de qualidade; caso contrário
fica `quarantined` e a versão GOLD anterior continua ativa.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from rj_energy.models import (
    GateDecision,
    LifecycleStatus,
    RawFileRecord,
    ValidationOutcome,
)

MANIFEST_SCHEMA: dict[str, pl.PolarsDataType] = {
    "source": pl.Utf8,
    "dataset": pl.Utf8,
    "package_id": pl.Utf8,
    "resource_id": pl.Utf8,
    "resource_name": pl.Utf8,
    "reference_period": pl.Utf8,
    "format": pl.Utf8,
    "download_url": pl.Utf8,
    "source_published_at": pl.Utf8,
    "source_modified_at": pl.Utf8,
    "retrieved_at": pl.Utf8,
    "hash_sha256": pl.Utf8,
    "etag": pl.Utf8,
    "last_modified_http": pl.Utf8,
    "file_size": pl.Int64,
    "schema_hash": pl.Utf8,
    "row_count": pl.Int64,
    "validation_status": pl.Utf8,
    "lifecycle_status": pl.Utf8,
    "is_latest_downloaded": pl.Boolean,
    "is_latest_valid": pl.Boolean,
    "is_active_for_gold": pl.Boolean,
    "processing_version": pl.Utf8,
    "local_path": pl.Utf8,
    "quarantine_reason": pl.Utf8,
}

REVISION_LOG_SCHEMA: dict[str, pl.PolarsDataType] = {
    "source": pl.Utf8,
    "dataset": pl.Utf8,
    "resource_id": pl.Utf8,
    "reference_period": pl.Utf8,
    "old_hash": pl.Utf8,
    "new_hash": pl.Utf8,
    "detected_at": pl.Utf8,
    "rows_added": pl.Int64,
    "rows_removed": pl.Int64,
    "rows_changed": pl.Int64,
    "downstream_reprocessed": pl.Boolean,
}


def empty_manifest() -> pl.DataFrame:
    return pl.DataFrame(schema=MANIFEST_SCHEMA)


def empty_revision_log() -> pl.DataFrame:
    return pl.DataFrame(schema=REVISION_LOG_SCHEMA)


def load_manifest(path: Path) -> pl.DataFrame:
    if not path.exists():
        return empty_manifest()
    return pl.read_parquet(path)


def save_manifest(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)


def find_existing(df: pl.DataFrame, source: str, resource_id: str, hash_sha256: str) -> pl.DataFrame:
    """Retorna as linhas já existentes no manifest com mesmo hash (evita redownload / duplicatas)."""
    if df.is_empty():
        return df
    return df.filter(
        (pl.col("source") == source) & (pl.col("resource_id") == resource_id) & (pl.col("hash_sha256") == hash_sha256)
    )


def detect_revision(df: pl.DataFrame, source: str, resource_id: str, reference_period: str | None, new_hash: str) -> str | None:
    """Retorna o hash antigo se o mesmo resource_id/período já existir com hash diferente (revisão histórica)."""
    if df.is_empty():
        return None
    existing = df.filter(
        (pl.col("source") == source)
        & (pl.col("resource_id") == resource_id)
        & (pl.col("reference_period").eq_missing(reference_period))
        & (pl.col("is_latest_downloaded"))
    )
    if existing.is_empty():
        return None
    old_hash = existing.sort("retrieved_at", descending=True).row(0, named=True)["hash_sha256"]
    return old_hash if old_hash != new_hash else None


def append_entry(df: pl.DataFrame, entry: RawFileRecord) -> pl.DataFrame:
    """Adiciona uma nova versão ao manifest, sem nunca sobrescrever ou apagar linhas anteriores.

    Rebaixa `is_latest_downloaded` das versões anteriores do mesmo (source, resource_id,
    reference_period) para False, e insere a nova linha como a mais recente baixada.
    """
    row = {**entry.model_dump(), "quarantine_reason": None}
    new_row = pl.DataFrame([row], schema=MANIFEST_SCHEMA)

    if df.is_empty():
        return new_row

    mask = (
        (pl.col("source") == entry.source)
        & (pl.col("resource_id") == entry.resource_id)
        & (pl.col("reference_period").eq_missing(entry.reference_period))
    )
    updated = df.with_columns(pl.when(mask).then(False).otherwise(pl.col("is_latest_downloaded")).alias("is_latest_downloaded"))
    return pl.concat([updated, new_row], how="vertical")


def apply_gate_decision(df: pl.DataFrame, decision: GateDecision) -> pl.DataFrame:
    """Aplica o resultado do gate de promoção (spec seção 24): promove para ACTIVE
    ou coloca em QUARANTINED, sem nunca remover a versão GOLD anterior até que a
    nova seja aprovada.
    """
    mask = pl.col("resource_id") == decision.resource_id

    if decision.approved:
        # Rebaixa qualquer versão ativa anterior do mesmo dataset/período para SUPERSEDED.
        target_row = df.filter(mask)
        if target_row.is_empty():
            raise ValueError(f"resource_id {decision.resource_id} não encontrado no manifest")
        target = target_row.row(0, named=True)
        supersede_mask = (
            (pl.col("source") == target["source"])
            & (pl.col("dataset") == target["dataset"])
            & (pl.col("reference_period").eq_missing(target["reference_period"]))
            & (pl.col("is_active_for_gold"))
            & (pl.col("resource_id") != decision.resource_id)
        )
        df = df.with_columns(
            pl.when(supersede_mask).then(pl.lit(LifecycleStatus.SUPERSEDED.value)).otherwise(pl.col("lifecycle_status")).alias("lifecycle_status"),
            pl.when(supersede_mask).then(False).otherwise(pl.col("is_active_for_gold")).alias("is_active_for_gold"),
        )
        df = df.with_columns(
            pl.when(mask).then(True).otherwise(pl.col("is_latest_valid")).alias("is_latest_valid"),
            pl.when(mask).then(True).otherwise(pl.col("is_active_for_gold")).alias("is_active_for_gold"),
            pl.when(mask).then(pl.lit(LifecycleStatus.ACTIVE.value)).otherwise(pl.col("lifecycle_status")).alias("lifecycle_status"),
            pl.when(mask).then(pl.lit(LifecycleStatus.VALIDATED.value)).otherwise(pl.col("validation_status")).alias("validation_status"),
        )
    else:
        reason = "; ".join(decision.reasons)
        df = df.with_columns(
            pl.when(mask).then(pl.lit(LifecycleStatus.QUARANTINED.value)).otherwise(pl.col("lifecycle_status")).alias("lifecycle_status"),
            pl.when(mask).then(pl.lit(LifecycleStatus.INVALID.value)).otherwise(pl.col("validation_status")).alias("validation_status"),
            pl.when(mask).then(pl.lit(reason)).otherwise(pl.col("quarantine_reason")).alias("quarantine_reason"),
        )
    return df


def evaluate_gate(resource_id: str, reference_period: str | None, outcomes: list[ValidationOutcome]) -> GateDecision:
    """Gate de promoção para GOLD (spec seção 24): só aprova se TODAS as checagens
    de severidade 'error' passarem. Warnings não bloqueiam, mas são registrados.
    """
    blocking_failures = [o for o in outcomes if not o.passed and o.severity == "error"]
    approved = len(blocking_failures) == 0
    reasons = [f"{o.check_name}: {o.details}" for o in blocking_failures]
    return GateDecision(
        resource_id=resource_id,
        reference_period=reference_period,
        approved=approved,
        reasons=reasons,
        outcomes=outcomes,
        decided_at=datetime.now(UTC),
    )


def get_active_for_gold(df: pl.DataFrame, source: str, dataset: str, reference_period: str | None = None) -> pl.DataFrame:
    if df.is_empty():
        return df
    mask = (pl.col("source") == source) & (pl.col("dataset") == dataset) & (pl.col("is_active_for_gold"))
    if reference_period is not None:
        mask = mask & (pl.col("reference_period") == reference_period)
    return df.filter(mask)


def append_revision(log_df: pl.DataFrame, *, source: str, dataset: str, resource_id: str, reference_period: str | None,
                     old_hash: str, new_hash: str, rows_added: int | None = None, rows_removed: int | None = None,
                     rows_changed: int | None = None, downstream_reprocessed: bool = False) -> pl.DataFrame:
    row = {
        "source": source,
        "dataset": dataset,
        "resource_id": resource_id,
        "reference_period": reference_period,
        "old_hash": old_hash,
        "new_hash": new_hash,
        "detected_at": datetime.now(UTC).isoformat(),
        "rows_added": rows_added,
        "rows_removed": rows_removed,
        "rows_changed": rows_changed,
        "downstream_reprocessed": downstream_reprocessed,
    }
    new_row = pl.DataFrame([row], schema=REVISION_LOG_SCHEMA)
    return new_row if log_df.is_empty() else pl.concat([log_df, new_row], how="vertical")
