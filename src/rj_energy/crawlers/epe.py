"""Crawler EPE — Consumo Mensal de Energia Elétrica (spec seção 2.4 e 18).

Não é CKAN: a descoberta é feita visitando a página de publicação e
verificando se o link de download ainda aponta para o mesmo arquivo. A
comparação de URL/tamanho/hash/`DataVersao` interna é o que efetivamente
decide se há uma nova versão (feita em `transform/epe_transform.py`, já que
`DataVersao` só é conhecida após abrir o XLSX).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import polars as pl

from rj_energy.config import PipelineConfig
from rj_energy.crawlers.base import download_and_register
from rj_energy.discovery.webpage import discover_current_download_link
from rj_energy.models import ResourceMetadata
from rj_energy.utils.http import PipelineHttpClient
from rj_energy.utils.logging import get_logger, log_event

logger = get_logger(__name__)

SOURCE = "epe"
DATASET = "consumo_mensal"


def discover(http: PipelineHttpClient, cfg: PipelineConfig) -> ResourceMetadata:
    src_cfg = cfg.source(SOURCE)
    url = discover_current_download_link(
        http,
        src_cfg["publication_page"],
        extensions=(".xlsx",),
        fallback_url=src_cfg["known_xlsx_url"],
    )
    # Sem CKAN, não há resource_id estável — deriva-se um id determinístico da URL,
    # para que o mesmo arquivo (mesmo link) sempre mapeie para o mesmo resource_id
    # no manifest, mesmo entre execuções diferentes.
    resource_id = f"epe-{hashlib.sha1(url.encode('utf-8')).hexdigest()[:16]}"
    log_event(logger, "epe_link_resolved", "Link de download EPE resolvido", url=url)
    return ResourceMetadata(id=resource_id, name="consumo_mensal_epe", format="xlsx", url=url, dataset=SOURCE)


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
