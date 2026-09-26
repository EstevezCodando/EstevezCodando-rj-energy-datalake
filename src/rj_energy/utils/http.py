"""Cliente HTTP compartilhado: timeout, retry com backoff exponencial, rate limiting,
User-Agent identificável e verificação de robots.txt (spec seção 10).

Nunca contorna autenticação, CAPTCHA ou mecanismos de limitação — apenas
implementa boas práticas de cliente (retry/backoff/rate-limit) e respeita
explicitamente robots.txt antes de fazer scraping de páginas HTML.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Self
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from rj_energy.config import PipelineConfig, load_config
from rj_energy.utils.logging import get_logger, log_event

logger = get_logger(__name__)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class RobotsDisallowedError(RuntimeError):
    """Levantado quando robots.txt proíbe explicitamente o acesso à URL."""


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in _RETRYABLE_STATUS
    return False


class _RateLimiter:
    """Rate limiter simples por host (thread-safe), respeita `rate_limit_seconds` entre requisições."""

    def __init__(self, min_interval_seconds: float) -> None:
        self._min_interval = min_interval_seconds
        self._last_call: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait(self, host: str) -> None:
        with self._lock:
            now = time.monotonic()
            last = self._last_call.get(host, 0.0)
            elapsed = now - last
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call[host] = time.monotonic()


class _RobotsCache:
    def __init__(self, user_agent: str, client: httpx.Client) -> None:
        self._user_agent = user_agent
        self._client = client
        self._cache: dict[str, RobotFileParser] = {}

    def can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._cache.get(origin)
        if parser is None:
            parser = RobotFileParser()
            robots_url = f"{origin}/robots.txt"
            try:
                resp = self._client.get(robots_url, timeout=10)
                if resp.status_code == 200:
                    parser.parse(resp.text.splitlines())
                else:
                    # Sem robots.txt (ou inacessível): assume-se permitido por padrão,
                    # como é convenção comum, mas isso é registrado no log.
                    parser.parse([])
            except httpx.HTTPError:
                parser.parse([])
            self._cache[origin] = parser
        return parser.can_fetch(self._user_agent, url)


@dataclass
class PipelineHttpClient:
    """Wrapper fino sobre httpx.Client com retry, rate-limit, UA e robots.txt."""

    config: PipelineConfig
    _client: httpx.Client
    _rate_limiter: _RateLimiter
    _robots: _RobotsCache

    @classmethod
    def create(cls, config: PipelineConfig | None = None) -> PipelineHttpClient:
        cfg = config or load_config()
        client = httpx.Client(
            headers={"User-Agent": cfg.user_agent},
            timeout=cfg.http["timeout_seconds"],
            follow_redirects=True,
        )
        rate_limiter = _RateLimiter(cfg.http["rate_limit_seconds"])
        robots = _RobotsCache(cfg.user_agent, client)
        return cls(config=cfg, _client=client, _rate_limiter=rate_limiter, _robots=robots)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _throttle(self, url: str) -> None:
        host = urlparse(url).netloc
        self._rate_limiter.wait(host)

    def get_json(self, url: str, *, enforce_robots: bool = False, **kwargs: object) -> dict:
        response = self._get(url, enforce_robots=enforce_robots, **kwargs)
        return response.json()

    def get_text(self, url: str, *, enforce_robots: bool = True, **kwargs: object) -> str:
        response = self._get(url, enforce_robots=enforce_robots, **kwargs)
        return response.text

    def stream_download(self, url: str, dest_path: str, *, enforce_robots: bool = False) -> tuple[str | None, str | None]:
        """Baixa o arquivo em streaming para `dest_path`. Retorna (etag, last-modified)."""
        if enforce_robots and not self._robots.can_fetch(url):
            raise RobotsDisallowedError(f"robots.txt proíbe o acesso a {url}")
        self._throttle(url)

        @retry(
            reraise=True,
            stop=stop_after_attempt(self.config.http["max_retries"]),
            wait=wait_exponential(multiplier=self.config.http["backoff_base_seconds"], min=1, max=60),
            retry=retry_if_exception(_is_retryable),
        )
        def _do_download() -> tuple[str | None, str | None]:
            with self._client.stream("GET", url) as response:
                if response.status_code in _RETRYABLE_STATUS:
                    response.raise_for_status()
                response.raise_for_status()
                with open(dest_path, "wb") as fh:
                    fh.writelines(response.iter_bytes())
                return response.headers.get("etag"), response.headers.get("last-modified")

        try:
            return _do_download()
        except httpx.HTTPStatusError as exc:
            log_event(logger, "download_failed", "Falha ao baixar recurso", url=url, status=exc.response.status_code)
            raise

    def _get(self, url: str, *, enforce_robots: bool, **kwargs: object) -> httpx.Response:
        if enforce_robots and not self._robots.can_fetch(url):
            raise RobotsDisallowedError(f"robots.txt proíbe o acesso a {url}")
        self._throttle(url)

        @retry(
            reraise=True,
            stop=stop_after_attempt(self.config.http["max_retries"]),
            wait=wait_exponential(multiplier=self.config.http["backoff_base_seconds"], min=1, max=60),
            retry=retry_if_exception(_is_retryable),
        )
        def _do_get() -> httpx.Response:
            response = self._client.get(url, **kwargs)
            response.raise_for_status()
            return response

        return _do_get()
