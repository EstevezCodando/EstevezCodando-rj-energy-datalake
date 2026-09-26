"""Crawler ANEEL — CTR Curva de Carga (spec seção 2.1 e 16).

Descoberta via CKAN `package_show`; fallback para as URLs diretas conhecidas
(config/sources.yaml) apenas se a descoberta dinâmica falhar — nesse caso o
recurso é marcado com `discovery_method=known_url_fallback` no log.
"""

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

SOURCE = "aneel_ctr"
SUB_DATASETS = ("consumidor_tipo", "redes_tipo")


def discover(http: PipelineHttpClient, cfg: PipelineConfig) -> dict[str, ResourceMetadata]:
    """Retorna o recurso preferido (Parquet > CSV) para cada sub-dataset (consumidor-tipo, redes-tipo)."""
    src_cfg = cfg.source(SOURCE)
    selected: dict[str, ResourceMetadata] = {}
    try:
        resources = discover_package_resources(http, src_cfg["ckan_package_show"], dataset=SOURCE)
        for sub in SUB_DATASETS:
            name_hint = "consumidor" if sub == "consumidor_tipo" else "redes"
            picked = select_preferred_resource(resources, cfg.format_preference, name_filter=name_hint)
            if picked is not None:
                selected[sub] = picked
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "ckan_discovery_failed", "Falha na descoberta CKAN, usando fallback de URLs conhecidas",
                   source=SOURCE, error=str(exc))

    for sub, key in (("consumidor_tipo", "consumidor_tipo_parquet"), ("redes_tipo", "redes_tipo_parquet")):
        if sub not in selected:
            known = src_cfg["known_resources"][key]
            selected[sub] = ResourceMetadata(
                id=known["resource_id"],
                name=f"{sub}_fallback",
                format="parquet",
                url=known["url"],
                package_id=src_cfg["package_id"],
                dataset=SOURCE,
            )
            log_event(logger, "fallback_used", "Usando URL conhecida (fallback) para recurso", source=SOURCE, sub_dataset=sub)
    return selected


def crawl(
    http: PipelineHttpClient,
    cfg: PipelineConfig,
    raw_root: Path,
    manifest: pl.DataFrame,
    revision_log: pl.DataFrame,
    processing_version: str = "0.1.0",
) -> tuple[pl.DataFrame, pl.DataFrame, list[Path]]:
    selected = discover(http, cfg)
    raw_dir = raw_root / SOURCE
    downloaded_paths: list[Path] = []

    for sub_dataset, resource in selected.items():
        manifest, revision_log, record, _reused = download_and_register(
            http,
            source=SOURCE,
            dataset=sub_dataset,
            resource=resource,
            reference_period=None,  # período real vem das colunas AnoPrcCal/DscTipoDia após parsing
            raw_dir=raw_dir,
            manifest=manifest,
            revision_log=revision_log,
            processing_version=processing_version,
        )
        if record is not None:
            downloaded_paths.append(Path(record.local_path))

    return manifest, revision_log, downloaded_paths
