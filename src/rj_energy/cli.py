"""CLI do pipeline (spec seção 36).

    python -m rj_energy discover
    python -m rj_energy freshness
    python -m rj_energy download
    python -m rj_energy validate
    python -m rj_energy transform
    python -m rj_energy build-gold
    python -m rj_energy revisions
    python -m rj_energy run-all
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated

import polars as pl
import typer

from rj_energy.config import DEFAULT_DATA_DIR, load_config
from rj_energy.discovery.ckan import discover_package_resources
from rj_energy.orchestration import (
    DataLakePaths,
    build_average_24h_reports,
    cmd_download,
    cmd_freshness,
    cmd_revisions,
    cmd_transform_aneel,
    cmd_transform_ons,
    cmd_transform_ons_national,
    cmd_validate,
)
from rj_energy.utils.http import PipelineHttpClient
from rj_energy.utils.logging import get_logger, log_event

app = typer.Typer(help="Pipeline de coleta e consolidação de dados de carga e consumo elétrico do RJ.")
logger = get_logger(__name__)


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _paths(output_dir: str | None) -> DataLakePaths:
    root = Path(output_dir) if output_dir else DEFAULT_DATA_DIR
    return DataLakePaths(root=root)


@app.command()
def discover(
    source: Annotated[str | None, typer.Option(help="Fonte específica (aneel_ctr|ons|ccee|epe|samp). Padrão: todas as CKAN.")] = None,
) -> None:
    """Consulta os catálogos oficiais e lista os recursos atualmente publicados, sem baixar nada."""
    cfg = load_config()
    ckan_sources = ["aneel_ctr", "ons", "ccee", "samp"]
    targets = [source] if source else ckan_sources
    with PipelineHttpClient.create(cfg) as http:
        for src in targets:
            if src not in ckan_sources:
                typer.echo(f"[{src}] descoberta via scraping (não-CKAN) — use 'download' para resolver o link atual.")
                continue
            src_cfg = cfg.source(src)
            try:
                resources = discover_package_resources(http, src_cfg["ckan_package_show"], dataset=src)
            except Exception as exc:  # noqa: BLE001 - uma fonte fora do ar não deve derrubar as demais
                typer.echo(f"[{src}] FALHA na descoberta: {exc}")
                continue
            typer.echo(f"[{src}] {len(resources)} recursos encontrados:")
            for r in resources:
                typer.echo(f"  - {r.name} ({r.format}) id={r.id} modificado={r.metadata_modified or r.last_modified or r.created}")


@app.command()
def freshness(output_dir: Annotated[str | None, typer.Option("--output-dir")] = None) -> None:
    """Gera o relatório de freshness (spec seção 32)."""
    paths = _paths(output_dir)
    df = cmd_freshness(paths)
    typer.echo(df)


@app.command()
def download(
    source: Annotated[str | None, typer.Option("--source")] = None,
    start_date: Annotated[str | None, typer.Option("--start-date")] = None,
    end_date: Annotated[str | None, typer.Option("--end-date")] = None,
    output_dir: Annotated[str | None, typer.Option("--output-dir")] = None,
    force_download: Annotated[bool, typer.Option("--force-download")] = False,
) -> None:
    """Descobre e baixa os recursos, registrando no manifest (spec seção 4)."""
    paths = _paths(output_dir)
    sources = [source] if source else None
    cmd_download(paths, sources=sources, start_date=_parse_date(start_date), end_date=_parse_date(end_date))
    typer.echo(f"Download concluído. Manifest em {paths.manifest_path}")


@app.command()
def validate(output_dir: Annotated[str | None, typer.Option("--output-dir")] = None) -> None:
    """Executa as checagens de qualidade e o gate de promoção para GOLD (spec seções 23-24)."""
    paths = _paths(output_dir)
    report = cmd_validate(paths)
    typer.echo(report)


def _transform_all(paths: DataLakePaths) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """RJ + nacional (soma dos 4 subsistemas) + ANEEL CTR — usado por
    `transform`, `build-gold` e `run-all` para não triplicar a lógica."""
    _30min, hourly_rj = cmd_transform_ons(paths)
    build_average_24h_reports(hourly_rj, paths, prefix="rj")
    hourly_brasil = cmd_transform_ons_national(paths)
    build_average_24h_reports(hourly_brasil, paths, prefix="brasil")
    aneel_curve = cmd_transform_aneel(paths)
    return hourly_rj, hourly_brasil, aneel_curve


@app.command()
def transform(output_dir: Annotated[str | None, typer.Option("--output-dir")] = None) -> None:
    """Converte RAW -> SILVER/GOLD para ONS (RJ + nacional) e ANEEL CTR (curvas)."""
    paths = _paths(output_dir)
    hourly_rj, hourly_brasil, aneel_curve = _transform_all(paths)
    typer.echo(
        f"ONS RJ: {hourly_rj.height if not hourly_rj.is_empty() else 0} linhas horárias. "
        f"ONS Brasil: {hourly_brasil.height if not hourly_brasil.is_empty() else 0} linhas horárias. "
        f"ANEEL CTR: {aneel_curve.height if not aneel_curve.is_empty() else 0} linhas de curva."
    )


@app.command(name="build-gold")
def build_gold(output_dir: Annotated[str | None, typer.Option("--output-dir")] = None) -> None:
    """Roda validate + transform e materializa os artefatos GOLD (spec seção 27)."""
    paths = _paths(output_dir)
    cmd_validate(paths)
    _transform_all(paths)
    cmd_freshness(paths)
    cmd_revisions(paths)
    typer.echo(f"GOLD atualizado em {paths.gold}")


@app.command()
def revisions(output_dir: Annotated[str | None, typer.Option("--output-dir")] = None) -> None:
    """Exporta o source_revision_log (spec seção 7)."""
    paths = _paths(output_dir)
    df = cmd_revisions(paths)
    typer.echo(df)


@app.command(name="run-all")
def run_all(
    start_date: Annotated[str | None, typer.Option("--start-date")] = None,
    end_date: Annotated[str | None, typer.Option("--end-date")] = None,
    source: Annotated[str | None, typer.Option("--source")] = None,
    output_dir: Annotated[str | None, typer.Option("--output-dir")] = None,
) -> None:
    """download -> validate -> transform -> build-gold -> freshness -> revisions."""
    paths = _paths(output_dir)
    sources = [source] if source else None
    log_event(logger, "run_all_start", "Iniciando execução completa do pipeline")
    cmd_download(paths, sources=sources, start_date=_parse_date(start_date), end_date=_parse_date(end_date))
    cmd_validate(paths)
    _transform_all(paths)
    cmd_freshness(paths)
    cmd_revisions(paths)
    log_event(logger, "run_all_complete", "Execução completa do pipeline finalizada")
    typer.echo(f"Pipeline completo. Saída em {paths.gold}")


if __name__ == "__main__":
    app()
