"""Crawler ONS — Carga de Energia Verificada, área geoelétrica RJ (spec seção 2.2 e 15).

A API `apicarga.ons.org.br` é consultada por janelas mensais. Além disso, o
pipeline reconsulta periodicamente os períodos recentes (janela de rechecagem
configurável, spec seção 8), pois a própria fonte informa que os dados passam
por consistências posteriores à publicação.
"""

from __future__ import annotations

import calendar
from datetime import date
from pathlib import Path

import polars as pl

from rj_energy.config import PipelineConfig
from rj_energy.crawlers.base import download_and_register
from rj_energy.discovery.ckan import discover_package_resources
from rj_energy.models import ResourceMetadata
from rj_energy.utils.http import PipelineHttpClient
from rj_energy.utils.logging import get_logger, log_event

logger = get_logger(__name__)

SOURCE = "ons"
DATASET = "carga_verificada"

# Subsistemas que, somados, equivalem à carga do SIN (Sistema Interligado
# Nacional) — confirmado por observação direta da API real: `cod_areacarga=SIN`
# existe mas retorna sempre zero (não é populado); o total nacional real é a
# SOMA dos 4 subsistemas abaixo em cada instante (nunca a média — carga
# nacional é a soma simultânea das cargas regionais, spec seção 15 aplicado
# por analogia).
NATIONAL_SUBSYSTEM_AREAS: tuple[str, ...] = ("S", "NE", "N", "SECO")


def discover_documentation(http: PipelineHttpClient, cfg: PipelineConfig) -> list[ResourceMetadata]:
    """Descobre os recursos de documentação/dicionário via CKAN (não é onde os
    dados em si ficam — a API é a fonte primária de dados, per spec seção 2.2)."""
    src_cfg = cfg.source(SOURCE)
    try:
        return discover_package_resources(http, src_cfg["ckan_package_show"], dataset=SOURCE)
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "ckan_discovery_failed", "Falha ao descobrir documentação ONS via CKAN", error=str(exc))
        return []


def iter_months(start: date, end: date) -> list[tuple[date, date]]:
    """Particiona o intervalo em janelas mensais (início, fim) inclusive."""
    windows: list[tuple[date, date]] = []
    cursor = date(start.year, start.month, 1)
    while cursor <= end:
        last_day = calendar.monthrange(cursor.year, cursor.month)[1]
        month_end = date(cursor.year, cursor.month, last_day)
        window_start = max(cursor, start)
        window_end = min(month_end, end)
        windows.append((window_start, window_end))
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    return windows


def build_api_resource(cfg: PipelineConfig, window_start: date, window_end: date, area_code: str) -> ResourceMetadata:
    src_cfg = cfg.source(SOURCE)
    url = (
        f"{src_cfg['api_base']}?dat_inicio={window_start.isoformat()}"
        f"&dat_fim={window_end.isoformat()}&cod_areacarga={area_code}"
    )
    resource_id = f"ons-{area_code}-{window_start.isoformat()}-{window_end.isoformat()}"
    return ResourceMetadata(
        id=resource_id,
        name=f"carga_verificada_{area_code}_{window_start.isoformat()}_{window_end.isoformat()}",
        format="json",
        url=url,
        dataset=f"{DATASET}_{area_code.lower()}",
    )


def crawl(
    http: PipelineHttpClient,
    cfg: PipelineConfig,
    raw_root: Path,
    manifest: pl.DataFrame,
    revision_log: pl.DataFrame,
    start_date: date,
    end_date: date,
    processing_version: str = "0.1.0",
    area_code: str | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, list[Path]]:
    """Baixa a área `area_code` (padrão: `area_carga` do config, historicamente
    RJ). Para o total nacional, chamar uma vez por área em
    `NATIONAL_SUBSYSTEM_AREAS` (ver `crawl_national_subsystems`)."""
    area = area_code or cfg.source(SOURCE)["area_carga"]
    dataset = f"{DATASET}_{area.lower()}"
    raw_dir = raw_root / SOURCE
    downloaded_paths: list[Path] = []

    for window_start, window_end in iter_months(start_date, end_date):
        resource = build_api_resource(cfg, window_start, window_end, area)
        reference_period = f"{window_start.year:04d}-{window_start.month:02d}"
        manifest, revision_log, record, _reused = download_and_register(
            http, source=SOURCE, dataset=dataset, resource=resource, reference_period=reference_period,
            raw_dir=raw_dir, manifest=manifest, revision_log=revision_log,
            processing_version=processing_version,
        )
        if record is not None:
            downloaded_paths.append(Path(record.local_path))

    return manifest, revision_log, downloaded_paths


def crawl_national_subsystems(
    http: PipelineHttpClient,
    cfg: PipelineConfig,
    raw_root: Path,
    manifest: pl.DataFrame,
    revision_log: pl.DataFrame,
    start_date: date,
    end_date: date,
    processing_version: str = "0.1.0",
) -> tuple[pl.DataFrame, pl.DataFrame, list[Path]]:
    """Baixa os 4 subsistemas que, somados, dão a carga total do Brasil (SIN)."""
    all_paths: list[Path] = []
    for area in NATIONAL_SUBSYSTEM_AREAS:
        manifest, revision_log, paths = crawl(
            http, cfg, raw_root, manifest, revision_log, start_date, end_date, processing_version, area_code=area
        )
        all_paths.extend(paths)
    return manifest, revision_log, all_paths


def months_needing_recheck(cfg: PipelineConfig, as_of: date) -> list[tuple[date, date]]:
    """Retorna as janelas mensais dentro da janela de rechecagem do ONS (spec seção 8),
    que devem ser CONSULTADAS NOVAMENTE mesmo se já baixadas antes, pois a fonte
    pode ter revisado os valores."""
    from datetime import timedelta

    window_days = cfg.recheck_window_days(SOURCE)
    recheck_start = as_of - timedelta(days=window_days)
    return iter_months(recheck_start, as_of)
