"""Orquestração genérica de coleta: download + hashing + registro no manifest +
detecção de revisão histórica (spec seções 4, 7, 37).

Cada crawler de fonte (aneel_ctr, ons, ccee, epe, samp) implementa apenas
`discover()`; este módulo cuida da parte comum (idempotência, hashing,
manifest, revision log).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from rj_energy.lifecycle.manifest import (
    append_entry,
    append_revision,
    detect_revision,
    find_existing,
)
from rj_energy.models import LifecycleStatus, RawFileRecord, ResourceMetadata
from rj_energy.utils.hashing import sha256_file
from rj_energy.utils.http import PipelineHttpClient
from rj_energy.utils.logging import get_logger, log_event

logger = get_logger(__name__)


@dataclass
class CrawlResult:
    manifest: pl.DataFrame
    revision_log: pl.DataFrame
    new_records: list[RawFileRecord]
    reused: list[str]  # resource_ids não baixados de novo (já presentes com mesmo hash)


def _local_path(raw_dir: Path, resource: ResourceMetadata) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    suffix = f".{resource.format}" if resource.format and "." not in resource.format else ""
    filename = f"{resource.id}{suffix}" if suffix else resource.id
    return raw_dir / filename


def download_and_register(
    http: PipelineHttpClient,
    *,
    source: str,
    dataset: str,
    resource: ResourceMetadata,
    reference_period: str | None,
    raw_dir: Path,
    manifest: pl.DataFrame,
    revision_log: pl.DataFrame,
    processing_version: str,
) -> tuple[pl.DataFrame, pl.DataFrame, RawFileRecord | None, bool]:
    """Baixa um recurso (se necessário), calcula hash, registra no manifest e
    detecta revisão histórica. Retorna (manifest, revision_log, record|None, reused).

    `record` é None e `reused=True` quando um download anterior com o MESMO
    hash já existe no manifest — nesse caso o arquivo não é baixado de novo
    (idempotência, spec seção 37), mas se o hash HTTP conhecido bater
    previamente isso só pode ser confirmado após o download real, então a
    heurística aqui é: sempre baixar, e comparar hash pós-download; downloads
    repetidos de arquivos idênticos são baratos e garantem correção.
    """
    dest_path = _local_path(raw_dir, resource)
    etag, last_modified_http = http.stream_download(resource.url, str(dest_path))

    file_hash = sha256_file(dest_path)
    file_size = dest_path.stat().st_size

    existing_same_hash = find_existing(manifest, source, resource.id, file_hash)
    if not existing_same_hash.is_empty():
        log_event(
            logger, "download_reused", "Recurso idêntico já presente no manifest (RAW preservado, sem duplicata)",
            source=source, resource_id=resource.id, hash=file_hash,
        )
        return manifest, revision_log, None, True

    old_hash = detect_revision(manifest, source, resource.id, reference_period, file_hash)

    record = RawFileRecord(
        source=source,
        dataset=dataset,
        resource_id=resource.id,
        resource_name=resource.name,
        reference_period=reference_period,
        format=resource.format,
        download_url=resource.url,
        # Relativo à raiz do datalake (data/), nunca um caminho absoluto do
        # sistema de arquivos local — portável entre máquinas/sessões e seguro
        # para publicação externa (ex.: dataset no Hugging Face).
        local_path=f"raw/{source}/{dest_path.name}",
        source_published_at=resource.created,
        source_modified_at=resource.metadata_modified or resource.last_modified,
        retrieved_at=datetime.now(UTC).isoformat(),
        hash_sha256=file_hash,
        etag=etag,
        last_modified_http=last_modified_http,
        file_size=file_size,
        validation_status=LifecycleStatus.DOWNLOADED.value,
        lifecycle_status=LifecycleStatus.RAW_IMMUTABLE.value,
        is_latest_downloaded=True,
        is_latest_valid=False,
        is_active_for_gold=False,
        processing_version=processing_version,
    )
    manifest = append_entry(manifest, record)

    if old_hash is not None:
        revision_log = append_revision(
            revision_log,
            source=source,
            dataset=dataset,
            resource_id=resource.id,
            reference_period=reference_period,
            old_hash=old_hash,
            new_hash=file_hash,
        )
        log_event(
            logger, "revision_detected", "Revisão histórica detectada: hash diferente para mesmo período",
            source=source, resource_id=resource.id, reference_period=reference_period,
        )

    log_event(logger, "download_ok", "Recurso baixado e registrado no manifest", source=source, resource_id=resource.id, size=file_size)
    return manifest, revision_log, record, False
