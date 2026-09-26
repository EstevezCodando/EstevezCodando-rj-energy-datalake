"""Carregamento da configuração central (config/sources.yaml).

Nenhum valor de negócio (URLs, package ids, janelas de rechecagem) deve ser
hardcodado na lógica do pipeline — tudo é lido a partir daqui, para que possa
ser ajustado sem alterar código (spec: seção 8).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "sources.yaml"
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"

_DURATION_RE = re.compile(r"^(\d+)([dm])$")


def parse_duration_to_days(value: str) -> int:
    """Converte '90d' -> 90, '6m' -> ~180 (30 dias por mês, aproximação declarada)."""
    match = _DURATION_RE.match(value.strip())
    if not match:
        raise ValueError(f"Duração inválida: {value!r}. Use formato '<N>d' ou '<N>m'.")
    amount, unit = match.groups()
    amount = int(amount)
    return amount if unit == "d" else amount * 30


@dataclass(frozen=True)
class PipelineConfig:
    raw: dict[str, Any]
    path: Path

    @property
    def sources(self) -> dict[str, Any]:
        return self.raw["sources"]

    @property
    def recheck_windows(self) -> dict[str, str]:
        return self.raw["recheck_windows"]

    def recheck_window_days(self, source: str) -> int:
        return parse_duration_to_days(self.recheck_windows[source])

    @property
    def user_agent(self) -> str:
        return self.raw["user_agent"]

    @property
    def http(self) -> dict[str, Any]:
        return self.raw["http"]

    @property
    def format_preference(self) -> list[str]:
        return self.raw["format_preference"]

    def source(self, name: str) -> dict[str, Any]:
        return self.sources[name]


@cache
def load_config(path: Path | None = None) -> PipelineConfig:
    cfg_path = path or DEFAULT_CONFIG_PATH
    with open(cfg_path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    return PipelineConfig(raw=raw, path=cfg_path)
