"""Descoberta dinâmica de recursos via API CKAN `package_show` (spec seção 9).

Nunca depende exclusivamente da página HTML do dataset — sempre prioriza o
endpoint `/api/3/action/package_show?id={PACKAGE_ID}`, que é a fonte de
verdade estável dos portais ANEEL, ONS e CCEE (todos rodam CKAN).
"""

from __future__ import annotations

from rj_energy.models import ResourceMetadata
from rj_energy.utils.http import PipelineHttpClient
from rj_energy.utils.logging import get_logger, log_event

logger = get_logger(__name__)


class CkanDiscoveryError(RuntimeError):
    pass


def discover_package_resources(
    http: PipelineHttpClient,
    package_show_url: str,
    *,
    dataset: str,
) -> list[ResourceMetadata]:
    """Chama `package_show` e retorna todos os recursos publicados no dataset."""
    payload = http.get_json(package_show_url)
    if not payload.get("success", False):
        raise CkanDiscoveryError(f"package_show retornou success=false para {package_show_url}")

    result = payload["result"]
    package_id = result.get("id")
    resources = []
    for res in result.get("resources", []):
        resources.append(
            ResourceMetadata(
                id=res["id"],
                name=res.get("name") or res["id"],
                format=(res.get("format") or "").lower(),
                url=res["url"],
                created=res.get("created"),
                last_modified=res.get("last_modified"),
                metadata_modified=res.get("metadata_modified"),
                hash=res.get("hash") or None,
                size=res.get("size"),
                mimetype=res.get("mimetype"),
                state=res.get("state"),
                package_id=package_id,
                dataset=dataset,
            )
        )
    log_event(logger, "ckan_discovery", "Recursos descobertos via CKAN", dataset=dataset, count=len(resources))
    return resources


def select_preferred_resource(
    resources: list[ResourceMetadata],
    format_preference: list[str],
    *,
    name_filter: str | None = None,
) -> ResourceMetadata | None:
    """Seleciona o recurso mais atual respeitando a ordem de preferência de formato
    (Parquet > CSV > JSON > XLSX > GZIP > HTML — spec seção 9), opcionalmente
    filtrando por substring no nome (para distinguir 'consumidor-tipo' de
    'redes-tipo', por exemplo).
    """
    candidates = resources
    if name_filter is not None:
        candidates = [r for r in candidates if name_filter.lower() in r.name.lower()]
    if not candidates:
        return None

    def recency_key(resource: ResourceMetadata) -> str:
        return resource.metadata_modified or resource.last_modified or resource.created or ""

    def format_rank(resource: ResourceMetadata) -> int:
        try:
            return format_preference.index(resource.format)
        except ValueError:
            return len(format_preference)

    # Ordena por recência (mais recente primeiro) e depois seleciona, de forma
    # estável, o de maior prioridade de formato — em empate de formato, prevalece
    # o mais recente (pela ordenação prévia).
    by_recency_desc = sorted(candidates, key=recency_key, reverse=True)
    return min(by_recency_desc, key=format_rank)


def latest_by_recency(resources: list[ResourceMetadata]) -> list[ResourceMetadata]:
    """Ordena recursos do mais recente para o mais antigo por metadata_modified/last_modified/created."""
    def key(resource: ResourceMetadata) -> str:
        return resource.metadata_modified or resource.last_modified or resource.created or ""

    return sorted(resources, key=key, reverse=True)
