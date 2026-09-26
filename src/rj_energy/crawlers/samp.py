"""Crawler ANEEL — SAMP Balanço (spec seção 2.5 e 19). Usado como controle e
validação cruzada (não substitui as demais bases)."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from rj_energy.config import PipelineConfig
from rj_energy.crawlers.base import download_and_register
from rj_energy.discovery.ckan import (
    discover_package_resources,
    select_preferred_resource,
)
from rj_energy.models import ResourceMetadata
from rj_energy.utils.http import PipelineHttpClient
from rj_energy.utils.logging import get_logger, log_event

logger = get_logger(__name__)

SOURCE = "samp"
DATASET = "balanco"


def discover(http: PipelineHttpClient, cfg: PipelineConfig) -> ResourceMetadata:
    src_cfg = cfg.source(SOURCE)
    try:
        resources = discover_package_resources(http, src_cfg["ckan_package_show"], dataset=SOURCE)
        picked = select_preferred_resource(resources, cfg.format_preference)
        if picked is not None:
            return picked
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "ckan_discovery_failed", "Falha na descoberta CKAN, usando fallback", source=SOURCE, error=str(exc))

    known = src_cfg["known_resources"]["parquet"]
    log_event(logger, "fallback_used", "Usando URL conhecida (fallback)", source=SOURCE)
    return ResourceMetadata(
        id=known["resource_id"], name="samp_balanco_fallback", format="parquet",
        url=known["url"], package_id=src_cfg["package_id"], dataset=SOURCE,
    )


def crawl(
    http: PipelineHttpClient,
    cfg: PipelineConfig,
    raw_root: Path,
    manifest: pl.DataFrame,
    revision_log: pl.DataFrame,
    processing_version: str = "0.1.0",
) -> tuple[pl.DataFrame, pl.DataFrame, list[Path]]:
    resource = discover(http, cfg)
    manifest, revision_log, record, _reused = download_and_register(
        http, source=SOURCE, dataset=DATASET, resource=resource, reference_period=None,
        raw_dir=raw_root / SOURCE, manifest=manifest, revision_log=revision_log,
        processing_version=processing_version,
    )
    paths = [Path(record.local_path)] if record is not None else []
    return manifest, revision_log, paths
