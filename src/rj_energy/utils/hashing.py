"""Hashing determinístico de arquivos e de schemas (spec seção 7)."""

from __future__ import annotations

import hashlib
from pathlib import Path

_CHUNK_SIZE = 1024 * 1024


def sha256_file(path: str | Path) -> str:
    """Calcula SHA-256 de um arquivo em streaming, sem carregá-lo inteiro na memória."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def schema_hash(column_names: list[str], column_types: list[str]) -> str:
    """Hash estável do schema (nomes + tipos, ordem preservada) para detectar schema drift."""
    payload = "|".join(f"{name}:{dtype}" for name, dtype in zip(column_names, column_types, strict=True))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
