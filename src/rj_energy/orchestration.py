"""Orquestração de alto nível do pipeline — usada pela CLI (spec seções 3, 4, 27, 32).

Cada função aqui corresponde a um comando da CLI (`discover`, `download`,
`validate`, `transform`, `build-gold`, `revisions`, `freshness`, `run-all`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl

from rj_energy.config import PipelineConfig, load_config
from rj_energy.crawlers import aneel_ctr, ccee, epe, ons, samp
from rj_energy.lifecycle.manifest import (
    apply_gate_decision,
    empty_revision_log,
    evaluate_gate,
    load_manifest,
    save_manifest,
)
from rj_energy.transform import aneel_transform, ons_transform
from rj_energy.utils.http import PipelineHttpClient
from rj_energy.utils.logging import get_logger, log_event
from rj_energy.validation import checks

logger = get_logger(__name__)

PROCESSING_VERSION = "0.1.0"

EXPECTED_FRESHNESS_LAG_DAYS = {
    "ons": 3,
    "ccee": 45,
    "epe": 60,
    "samp": 60,
    "aneel_ctr": 400,
}


@dataclass
class DataLakePaths:
    root: Path

    @property
    def raw(self) -> Path:
        return self.root / "raw"

    @property
    def bronze(self) -> Path:
        return self.root / "bronze"

    @property
    def silver(self) -> Path:
        return self.root / "silver"

    @property
    def gold(self) -> Path:
        return self.root / "gold"

    @property
    def metadata(self) -> Path:
        return self.root / "metadata"

    @property
    def quarantine(self) -> Path:
        return self.root / "quarantine"

    @property
    def manifest_path(self) -> Path:
        return self.metadata / "manifest.parquet"

    @property
    def revision_log_path(self) -> Path:
        return self.metadata / "source_revision_log.parquet"

    @property
    def lineage_path(self) -> Path:
        return self.metadata / "gold_dataset_lineage.parquet"


def _ensure_dirs(paths: DataLakePaths) -> None:
    for d in (paths.raw, paths.bronze, paths.silver, paths.gold, paths.metadata, paths.quarantine):
        d.mkdir(parents=True, exist_ok=True)


def cmd_download(
    paths: DataLakePaths,
    *,
    sources: list[str] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    cfg: PipelineConfig | None = None,
) -> None:
    """Descobre e baixa recursos das fontes selecionadas, registrando no manifest
    (spec seção 4, passos 1-7)."""
    _ensure_dirs(paths)
    cfg = cfg or load_config()
    manifest = load_manifest(paths.manifest_path)
    revision_log = load_manifest(paths.revision_log_path) if paths.revision_log_path.exists() else empty_revision_log()

    active_sources = sources or ["aneel_ctr", "ons", "ccee", "epe", "samp"]
    end_date = end_date or datetime.now(UTC).date()
    start_date = start_date or end_date.replace(day=1)

    failed_sources: dict[str, str] = {}

    def _run(name: str, fn) -> None:
        nonlocal manifest, revision_log
        if name not in active_sources:
            return
        try:
            manifest, revision_log, _ = fn()
        except Exception as exc:  # noqa: BLE001 - uma fonte fora do ar não pode impedir as demais
            failed_sources[name] = str(exc)
            log_event(logger, "source_download_failed", "Falha ao baixar fonte; demais fontes seguem normalmente", source=name, error=str(exc))

    with PipelineHttpClient.create(cfg) as http:
        _run("aneel_ctr", lambda: aneel_ctr.crawl(http, cfg, paths.raw, manifest, revision_log, PROCESSING_VERSION))
        _run("samp", lambda: samp.crawl(http, cfg, paths.raw, manifest, revision_log, PROCESSING_VERSION))
        _run("epe", lambda: epe.crawl(http, cfg, paths.raw, manifest, revision_log, PROCESSING_VERSION))
        _run("ccee", lambda: ccee.crawl(http, cfg, paths.raw, manifest, revision_log, PROCESSING_VERSION))
        _run("ons", lambda: ons.crawl(http, cfg, paths.raw, manifest, revision_log, start_date, end_date, PROCESSING_VERSION))

    save_manifest(manifest, paths.manifest_path)
    save_manifest(revision_log, paths.revision_log_path)
    log_event(logger, "download_complete", "Download concluído", sources=active_sources, failed=list(failed_sources))
    if failed_sources:
        for name, error in failed_sources.items():
            log_event(logger, "source_unavailable", "Fonte indisponível nesta execução", source=name, error=error)


def cmd_validate(paths: DataLakePaths, *, cfg: PipelineConfig | None = None) -> pl.DataFrame:
    """Roda as checagens de qualidade sobre as versões RAW mais recentes e aplica
    o gate de promoção para GOLD (spec seções 23-24). Retorna o data quality report."""
    cfg = cfg or load_config()
    manifest = load_manifest(paths.manifest_path)
    report_rows: list[dict] = []

    if manifest.is_empty():
        return pl.DataFrame(report_rows)

    latest_downloaded = manifest.filter(pl.col("is_latest_downloaded"))
    for row in latest_downloaded.iter_rows(named=True):
        outcomes = [
            checks.check_not_empty(pl.DataFrame({"x": [1]}) if row["row_count"] != 0 else pl.DataFrame()),
        ]
        # Checagens específicas por schema/tipo de recurso são aplicadas nos módulos
        # transform.*; aqui aplicamos as checagens genéricas de nível de arquivo.
        file_exists = (paths.root / row["local_path"]).exists()
        outcomes.append(
            checks.check_not_empty(pl.DataFrame({"x": [1]}) if file_exists else pl.DataFrame())
        )
        decision = evaluate_gate(row["resource_id"], row["reference_period"], outcomes)
        manifest = apply_gate_decision(manifest, decision)

        for outcome in outcomes:
            report_rows.append({
                "source": row["source"],
                "dataset": row["dataset"],
                "resource_id": row["resource_id"],
                "reference_period": row["reference_period"],
                "check_name": outcome.check_name,
                "passed": outcome.passed,
                "severity": outcome.severity,
                "details": outcome.details,
            })

    save_manifest(manifest, paths.manifest_path)
    report_df = pl.DataFrame(report_rows)
    report_df.write_csv(paths.gold / "data_quality_report.csv") if not report_df.is_empty() else None
    log_event(logger, "validate_complete", "Validação concluída", n_checks=len(report_rows))
    return report_df


def cmd_freshness(paths: DataLakePaths, *, cfg: PipelineConfig | None = None) -> pl.DataFrame:
    """Gera o relatório de freshness (spec seção 32-33)."""
    cfg = cfg or load_config()
    manifest = load_manifest(paths.manifest_path)
    now = datetime.now(UTC)
    rows = []

    # "aneel_distribuidoras" é apenas referência auxiliar (spec seção 2.6, sem
    # crawler/coleta próprios) — não entra no relatório de freshness de dados.
    collectible_sources = [s for s in cfg.sources if s != "aneel_distribuidoras"]

    for source in collectible_sources:
        source_rows = manifest.filter(pl.col("source") == source) if not manifest.is_empty() else manifest
        if source_rows.is_empty():
            rows.append({
                "source": source,
                "latest_reference_period": None,
                "latest_source_update": None,
                "last_checked_at": now.isoformat(),
                "last_successful_download": None,
                "latest_downloaded_version": None,
                "latest_valid_version": None,
                "days_since_latest_reference": None,
                "freshness_status": "source_unavailable",
                "validation_status": "n/a",
            })
            continue

        latest_downloaded = source_rows.filter(pl.col("is_latest_downloaded")).sort("retrieved_at", descending=True)
        latest_valid = source_rows.filter(pl.col("is_latest_valid")).sort("retrieved_at", descending=True)

        latest_row = latest_downloaded.row(0, named=True) if not latest_downloaded.is_empty() else None
        valid_row = latest_valid.row(0, named=True) if not latest_valid.is_empty() else None

        expected_lag = EXPECTED_FRESHNESS_LAG_DAYS.get(source, 30)
        days_since = None
        status = "fresh"
        if latest_row and latest_row.get("retrieved_at"):
            retrieved = datetime.fromisoformat(latest_row["retrieved_at"])
            days_since = (now - retrieved).days
            if valid_row is None:
                status = "new_version_pending_validation" if latest_row else "source_unavailable"
            elif days_since > expected_lag:
                status = "stale"
            elif days_since > expected_lag * 0.5:
                status = "expected_lag"
            else:
                status = "fresh"

        rows.append({
            "source": source,
            "latest_reference_period": latest_row["reference_period"] if latest_row else None,
            "latest_source_update": latest_row["source_modified_at"] if latest_row else None,
            "last_checked_at": now.isoformat(),
            "last_successful_download": latest_row["retrieved_at"] if latest_row else None,
            "latest_downloaded_version": latest_row["resource_id"] if latest_row else None,
            "latest_valid_version": valid_row["resource_id"] if valid_row else None,
            "days_since_latest_reference": days_since,
            "freshness_status": status,
            "validation_status": latest_row["validation_status"] if latest_row else "n/a",
        })

    df = pl.DataFrame(rows)
    paths.gold.mkdir(parents=True, exist_ok=True)
    df.write_csv(paths.gold / "data_freshness_report.csv")
    log_event(logger, "freshness_complete", "Relatório de freshness gerado", n_sources=len(rows))
    return df


def cmd_revisions(paths: DataLakePaths) -> pl.DataFrame:
    """Exporta o `source_revision_log` (spec seção 7)."""
    revision_log = load_manifest(paths.revision_log_path) if paths.revision_log_path.exists() else empty_revision_log()
    paths.gold.mkdir(parents=True, exist_ok=True)
    revision_log.write_csv(paths.gold / "source_revision_log.csv") if not revision_log.is_empty() else empty_revision_log().write_csv(
        paths.gold / "source_revision_log.csv"
    )
    return revision_log


def cmd_transform_ons(paths: DataLakePaths) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Transforma todos os arquivos RAW ONS `is_latest_downloaded` em SILVER
    (30 min e horário), e persiste em `data/silver/` e `data/gold/`."""
    manifest = load_manifest(paths.manifest_path)
    ons_rows = manifest.filter((pl.col("source") == "ons") & (pl.col("is_latest_downloaded")))

    all_30min = []
    for row in ons_rows.iter_rows(named=True):
        raw_path = paths.root / row["local_path"]
        if not raw_path.exists():
            continue
        raw_df = ons_transform.parse_raw_json(raw_path)
        silver_30min = ons_transform.to_silver_30min(raw_df, source_resource_id=row["resource_id"], retrieved_at=row["retrieved_at"])
        all_30min.append(silver_30min)

    if not all_30min:
        return pl.DataFrame(), pl.DataFrame()

    combined_30min = pl.concat(all_30min, how="diagonal_relaxed").unique(subset=["din_referenciautc"])
    combined_hourly = ons_transform.aggregate_hourly(combined_30min)

    paths.silver.mkdir(parents=True, exist_ok=True)
    paths.gold.mkdir(parents=True, exist_ok=True)
    combined_30min.write_parquet(paths.gold / "rj_load_30min.parquet")
    combined_hourly.write_parquet(paths.gold / "rj_load_hourly.parquet")

    return combined_30min, combined_hourly


def cmd_transform_aneel(paths: DataLakePaths) -> pl.DataFrame:
    """Transforma o arquivo RAW ANEEL CTR (consumidor-tipo) mais recente em curvas
    normalizadas (spec seção 16)."""
    manifest = load_manifest(paths.manifest_path)
    rows = manifest.filter(
        (pl.col("source") == "aneel_ctr") & (pl.col("dataset") == "consumidor_tipo") & (pl.col("is_latest_downloaded"))
    )
    if rows.is_empty():
        return pl.DataFrame()

    raw_path = paths.root / rows.sort("retrieved_at", descending=True).row(0, named=True)["local_path"]
    if not raw_path.exists():
        return pl.DataFrame()

    df = aneel_transform.load_consumidor_tipo(raw_path)
    stats = aneel_transform.build_curve_stats(df)
    normalized = aneel_transform.normalize_curve(stats)

    paths.silver.mkdir(parents=True, exist_ok=True)
    normalized.write_parquet(paths.silver / "aneel_ctr_curve_stats.parquet")
    return normalized


def build_average_24h_reports(hourly: pl.DataFrame, paths: DataLakePaths) -> None:
    """Produz rj_average_24h.csv, rj_average_24h_by_day_type.csv e
    rj_average_24h_by_month.csv (spec seções 27, 29)."""
    if hourly.is_empty():
        return
    paths.gold.mkdir(parents=True, exist_ok=True)

    overall = hourly.group_by("hour").agg(
        pl.col("load_hourly_mw").mean().alias("avg_mw"),
        pl.col("load_hourly_mw").median().alias("median_mw"),
        pl.col("load_hourly_mw").quantile(0.05).alias("p05_mw"),
        pl.col("load_hourly_mw").quantile(0.95).alias("p95_mw"),
    ).sort("hour")
    daily_mean = float(overall["avg_mw"].mean())
    overall = overall.with_columns((pl.col("avg_mw") / daily_mean).alias("normalized_load"))
    overall.write_csv(paths.gold / "rj_average_24h.csv")

    by_day_type = hourly.group_by(["day_type", "hour"]).agg(
        pl.col("load_hourly_mw").mean().alias("avg_mw"),
        pl.col("load_hourly_mw").median().alias("median_mw"),
        pl.col("load_hourly_mw").quantile(0.05).alias("p05_mw"),
        pl.col("load_hourly_mw").quantile(0.95).alias("p95_mw"),
    ).sort(["day_type", "hour"])
    by_day_type.write_csv(paths.gold / "rj_average_24h_by_day_type.csv")

    by_month = hourly.group_by(["month", "hour"]).agg(
        pl.col("load_hourly_mw").mean().alias("avg_mw"),
        pl.col("load_hourly_mw").median().alias("median_mw"),
        pl.col("load_hourly_mw").quantile(0.05).alias("p05_mw"),
        pl.col("load_hourly_mw").quantile(0.95).alias("p95_mw"),
    ).sort(["month", "hour"])
    by_month.write_csv(paths.gold / "rj_average_24h_by_month.csv")


def build_residential_report(curve_stats: pl.DataFrame, residential_label: str, paths: DataLakePaths, *, class_col: str = "DscDemandante") -> pl.DataFrame:
    """rj_residential_average_24h.csv (spec seção 27). `residential_label` deve
    ser um valor confirmado por `aneel_transform.distinct_category_values()` —
    nunca um rótulo assumido a priori (spec seção 16)."""
    if curve_stats.is_empty():
        return curve_stats
    subset = curve_stats.filter(pl.col(class_col) == residential_label)
    report = subset.group_by("hour").agg(
        pl.col("mean_mw").mean().alias("avg_mw"),
        pl.col("normalized_load").mean().alias("normalized_load"),
    ).sort("hour")
    paths.gold.mkdir(parents=True, exist_ok=True)
    report.write_csv(paths.gold / "rj_residential_average_24h.csv")
    return report


def build_source_comparison(comparisons: list[dict], paths: DataLakePaths) -> pl.DataFrame:
    """source_comparison.csv (spec seções 27, 40): compara métricas equivalentes
    entre fontes (ex.: pico ONS observado vs. pico ANEEL-calibrado), preservando
    os valores originais e explicitando o escopo geográfico de cada um — nunca
    ajustando silenciosamente para forçar concordância."""
    df = pl.DataFrame(comparisons)
    paths.gold.mkdir(parents=True, exist_ok=True)
    df.write_csv(paths.gold / "source_comparison.csv")
    return df
