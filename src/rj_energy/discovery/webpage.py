"""Descoberta por scraping de página HTML — usada apenas quando não há API/catálogo
estruturado adequado (spec seção 1 e 10), como no caso da EPE (não é CKAN) e das
páginas de distribuidoras da ANEEL.
"""

from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from rj_energy.utils.http import PipelineHttpClient
from rj_energy.utils.logging import get_logger, log_event

logger = get_logger(__name__)


def find_links_by_extension(html: str, base_url: str, extensions: tuple[str, ...]) -> list[str]:
    """Extrai links absolutos de uma página cujo path termina com uma das extensões dadas."""
    soup = BeautifulSoup(html, "lxml")
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if href.lower().endswith(extensions):
            links.append(urljoin(base_url, href))
    return links


def discover_current_download_link(
    http: PipelineHttpClient,
    page_url: str,
    *,
    extensions: tuple[str, ...] = (".xlsx", ".xls", ".csv"),
    fallback_url: str | None = None,
) -> str:
    """Visita a página de publicação e retorna o link de download atualmente
    apontado por ela. Isso evita confiar cegamente em um nome de arquivo fixo
    (spec seção 18: 'não confiar apenas no nome fixo do XLSX').

    Se a página não puder ser lida (robots.txt, erro de rede) e um
    `fallback_url` for fornecido, ele é usado — mas o chamador deve marcar essa
    origem como `page_scrape_fallback` na proveniência.
    """
    try:
        html = http.get_text(page_url, enforce_robots=True)
    except Exception as exc:
        log_event(logger, "webpage_discovery_failed", "Falha ao ler página de publicação", url=page_url, error=str(exc))
        if fallback_url:
            return fallback_url
        raise

    links = find_links_by_extension(html, page_url, extensions)
    if not links:
        log_event(logger, "webpage_discovery_empty", "Nenhum link de download encontrado na página", url=page_url)
        if fallback_url:
            return fallback_url
        raise RuntimeError(f"Nenhum link com extensões {extensions} encontrado em {page_url}")

    log_event(logger, "webpage_discovery", "Link de download descoberto via scraping", url=page_url, found=links[0])
    return links[0]
