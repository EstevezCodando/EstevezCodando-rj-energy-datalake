"""Crawler CCEE — Consumo Horário por Perfil de Agente (spec seção 2.3 e 17).

A cada execução, descobre TODOS os meses disponíveis via `package_show` — nunca
assume que o último recurso conhecido no documento de especificação continua
sendo o mais atual, e nunca hardcoda a URL do GZIP (ela é opaca e pode mudar).
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

from rj_energy.config import PipelineConfig
from rj_energy.crawlers.base import download_and_register
from rj_energy.discovery.ckan import discover_package_resources
from rj_energy.models import ResourceMetadata
from rj_energy.utils.http import PipelineHttpClient
from rj_energy.utils.logging import get_logger, log_event

logger = get_logger(__name__)

SOURCE = "ccee"
DATASET = "consumo_horario_perfil_agente"

_MONTHS_PT = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}
_YYYY_MM_RE = re.compile(r"(20\d{2})[-_/]?(0[1-9]|1[0-2])")
_MONTH_NAME_RE = re.compile(
    r"(janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)"
    r"[\s_/-]*(?:de)?[\s_/-]*(20\d{2})",
    re.IGNORECASE,
)


def extract_reference_period(name: str) -> str | None:
    """Extrai o período de comercialização (YYYY-MM) do nome do recurso, de forma
    best-effort (spec: 'não presumir que o último recurso conhecido é o atual' —
    portanto o período é sempre extraído do nome real do recurso, não assumido)."""
    match = _YYYY_MM_RE.search(name)
    if match:
        return f"{match.group(1)}-{match.group(2)}"

    match = _MONTH_NAME_RE.search(name)
    if match:
        month_name = match.group(1).lower().replace("ç", "c")
        month = _MONTHS_PT.get(month_name)
        if month:
            return f"{match.group(2)}-{month:02d}"
    return None


def discover(http: PipelineHttpClient, cfg: PipelineConfig) -> list[ResourceMetadata]:
    src_cfg = cfg.source(SOURCE)
    resources = discover_package_resources(http, src_cfg["ckan_package_show"], dataset=SOURCE)
    unresolved = [r.name for r in resources if extract_reference_period(r.name) is None]
    if unresolved:
        log_event(logger, "ccee_period_unresolved", "Não foi possível inferir período para alguns recursos CCEE",
                   names=unresolved)
    return resources


def crawl(
    http: PipelineHttpClient,
    cfg: PipelineConfig,
    raw_root: Path,
    manifest: pl.DataFrame,
    revision_log: pl.DataFrame,
    processing_version: str = "0.1.0",
    start_period: str | None = None,
    end_period: str | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, list[Path]]:
    resources = discover(http, cfg)
    raw_dir = raw_root / SOURCE
    downloaded_paths: list[Path] = []

    for resource in resources:
        period = extract_reference_period(resource.name)
        if start_period and period and period < start_period:
            continue
        if end_period and period and period > end_period:
            continue

        manifest, revision_log, record, _reused = download_and_register(
            http, source=SOURCE, dataset=DATASET, resource=resource, reference_period=period,
            raw_dir=raw_dir, manifest=manifest, revision_log=revision_log,
            processing_version=processing_version,
        )
        if record is not None:
            downloaded_paths.append(Path(record.local_path))

    return manifest, revision_log, downloaded_paths
