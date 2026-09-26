"""Modelos de domínio compartilhados por todo o pipeline (spec seções 5, 6, 11, 13)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class LifecycleStatus(StrEnum):
    """Ciclo de vida de uma versão de um recurso (spec seção 5)."""

    DISCOVERED = "discovered"
    DOWNLOADED = "downloaded"
    RAW_IMMUTABLE = "raw_immutable"
    PARSED = "parsed"
    VALIDATED = "validated"
    INVALID = "invalid"
    QUARANTINED = "quarantined"
    NORMALIZED = "normalized"
    SILVER = "silver"
    CROSS_VALIDATED = "cross_validated"
    ACTIVE = "active"  # ativo na camada GOLD
    SUPERSEDED = "superseded"
    REPROCESSED = "reprocessed"
    DEPRECATED_SOURCE = "deprecated_source"


class ObservationType(StrEnum):
    OBSERVED = "observed"
    AGGREGATED = "aggregated"
    ESTIMATED = "estimated"
    CALIBRATED = "calibrated"
    INTERPOLATED = "interpolated"
    DERIVED = "derived"


class GeographicScope(StrEnum):
    RJ_STATE = "RJ_state"
    DISTRIBUTION_AREA = "distribution_area"
    ONS_LOAD_AREA = "ONS_load_area"
    AGENT = "agent"
    CONNECTION_POINT = "connection_point"
    MULTI_STATE_DISTRIBUTOR = "multi_state_distributor"


class GeographicPrecision(StrEnum):
    EXACT = "exact"
    DISTRIBUTOR_MULTI_STATE = "distributor_multi_state"
    APPROXIMATE = "approximate"


class ResourceMetadata(BaseModel):
    """Metadados de um recurso descoberto em um catálogo (CKAN ou scraping) — spec seção 9."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    format: str
    url: str
    created: str | None = None
    last_modified: str | None = None
    metadata_modified: str | None = None
    hash: str | None = None
    size: int | None = None
    mimetype: str | None = None
    state: str | None = None
    package_id: str | None = None
    dataset: str | None = None


class RawFileRecord(BaseModel):
    """Resultado de um download bruto, antes de qualquer parsing (spec seções 7, 13)."""

    source: str
    dataset: str
    resource_id: str
    resource_name: str
    reference_period: str | None
    format: str
    download_url: str
    local_path: str
    source_published_at: str | None = None
    source_modified_at: str | None = None
    retrieved_at: str
    hash_sha256: str
    etag: str | None = None
    last_modified_http: str | None = None
    file_size: int
    schema_hash: str | None = None
    row_count: int | None = None
    validation_status: str = LifecycleStatus.DOWNLOADED.value
    lifecycle_status: str = LifecycleStatus.DOWNLOADED.value
    is_latest_downloaded: bool = True
    is_latest_valid: bool = False
    is_active_for_gold: bool = False
    processing_version: str = "0.1.0"


class ValidationOutcome(BaseModel):
    """Resultado de uma checagem de qualidade (spec seção 23-24)."""

    check_name: str
    passed: bool
    severity: str = "error"  # "error" | "warning" | "info"
    details: str = ""
    rows_affected: int | None = None


class GateDecision(BaseModel):
    """Decisão do gate de promoção para GOLD (spec seção 24)."""

    resource_id: str
    reference_period: str | None
    approved: bool
    reasons: list[str] = Field(default_factory=list)
    outcomes: list[ValidationOutcome] = Field(default_factory=list)
    decided_at: datetime
