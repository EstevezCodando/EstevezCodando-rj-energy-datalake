#!/usr/bin/env python3
"""Publica a camada GOLD deste datalake como um dataset no Hugging Face Hub.

Requer:
- `pip install -e ".[publish]"` (instala `huggingface_hub`)
- variável de ambiente `HF_TOKEN` com um token de escrita
  (https://huggingface.co/settings/tokens)

Uso:
    python scripts/publish_to_huggingface.py --repo-id EstevezCodando/rj-energy-datalake
    python scripts/publish_to_huggingface.py --repo-id EstevezCodando/rj-energy-datalake --private
    python scripts/publish_to_huggingface.py --repo-id EstevezCodando/rj-energy-datalake --dry-run

Não sobrescreve nada além do que este script explicitamente envia: o
dataset card (`huggingface/README.md` -> `README.md`), `data/gold/` -> `gold/`
e os arquivos de manifest/lineage de `data/metadata/` -> `metadata/`. Os
arquivos RAW (`data/raw/`) nunca são publicados — são grandes, reproduzíveis
via `python -m rj_energy download`, e alguns podem estar sujeitos a licenças
que não permitem redistribuição do arquivo original tal como está.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

GOLD_FILES_TO_SKIP = {".gitkeep"}
METADATA_FILES_TO_PUBLISH = {"manifest.parquet", "source_revision_log.parquet"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-id", required=True, help="Namespace/nome do dataset no HF, ex.: EstevezCodando/rj-energy-datalake")
    parser.add_argument("--private", action="store_true", help="Cria/mantém o repositório como privado (padrão: público)")
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que seria enviado, sem chamar a API do Hugging Face")
    parser.add_argument("--commit-message", default="Atualiza dataset GOLD (rj-energy-datalake)")
    args = parser.parse_args()

    gold_dir = PROJECT_ROOT / "data" / "gold"
    metadata_dir = PROJECT_ROOT / "data" / "metadata"
    card_path = PROJECT_ROOT / "huggingface" / "README.md"

    gold_files = sorted(p for p in gold_dir.glob("*") if p.is_file() and p.name not in GOLD_FILES_TO_SKIP)
    metadata_files = sorted(p for p in metadata_dir.glob("*") if p.is_file() and p.name in METADATA_FILES_TO_PUBLISH)

    if not gold_files:
        print(f"Nenhum arquivo encontrado em {gold_dir} — rode `python -m rj_energy build-gold` primeiro.", file=sys.stderr)
        return 1
    if not card_path.exists():
        print(f"Dataset card não encontrado em {card_path}.", file=sys.stderr)
        return 1

    print(f"Repositório de destino: {args.repo_id} ({'privado' if args.private else 'público'})")
    print(f"README (dataset card): {card_path.relative_to(PROJECT_ROOT)} -> README.md")
    for f in gold_files:
        print(f"  gold:     {f.relative_to(PROJECT_ROOT)} -> gold/{f.name}")
    for f in metadata_files:
        print(f"  metadata: {f.relative_to(PROJECT_ROOT)} -> metadata/{f.name}")

    if args.dry_run:
        print("\n--dry-run: nada foi enviado.")
        return 0

    token = os.environ.get("HF_TOKEN")
    if not token:
        print(
            "\nVariável de ambiente HF_TOKEN não encontrada. Gere um token de escrita em "
            "https://huggingface.co/settings/tokens e configure-o nas variáveis de ambiente "
            "da sessão/ambiente antes de rodar este script.",
            file=sys.stderr,
        )
        return 1

    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("huggingface_hub não instalado. Rode: pip install -e \".[publish]\"", file=sys.stderr)
        return 1

    api = HfApi(token=token)
    api.create_repo(repo_id=args.repo_id, repo_type="dataset", private=args.private, exist_ok=True)

    api.upload_file(
        path_or_fileobj=str(card_path),
        path_in_repo="README.md",
        repo_id=args.repo_id,
        repo_type="dataset",
        commit_message=args.commit_message,
    )
    for f in gold_files:
        api.upload_file(
            path_or_fileobj=str(f),
            path_in_repo=f"gold/{f.name}",
            repo_id=args.repo_id,
            repo_type="dataset",
            commit_message=args.commit_message,
        )
    for f in metadata_files:
        api.upload_file(
            path_or_fileobj=str(f),
            path_in_repo=f"metadata/{f.name}",
            repo_id=args.repo_id,
            repo_type="dataset",
            commit_message=args.commit_message,
        )

    print(f"\nPublicado em https://huggingface.co/datasets/{args.repo_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
