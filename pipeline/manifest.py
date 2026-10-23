"""Corpus Manifest Generator and Verifier (P3.7).

Generates manifest.json with content hashes, corpus metadata, taxonomy version,
and embedder specifications. Validates alignment at application startup.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pipeline.taxonomy import TaxonomyRegistry

DEFAULT_EMBEDDER_MODEL = "EmbeddingGemma"
DEFAULT_EMBEDDING_DIM = 768
DEFAULT_QUERY_PREFIX = "task: search query | query: "
DEFAULT_DOC_PREFIX = "task: search document | document: "


def compute_dir_hash(directory: Path, pattern: str = "*.md") -> str:
    """Compute deterministic SHA-256 hash of all matching files in directory."""
    hasher = hashlib.sha256()
    for p in sorted(directory.glob(pattern)):
        if p.name.startswith("_"):
            continue
        hasher.update(p.name.encode("utf-8"))
        hasher.update(p.read_bytes())
    return hasher.hexdigest()


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a single file."""
    if not filepath.exists():
        return ""
    return hashlib.sha256(filepath.read_bytes()).hexdigest()


class CorpusManifestManager:
    """Manages creation and verification of the corpus manifest.json."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = Path(repo_root or Path(__file__).resolve().parent.parent)
        self.corpora_dir = self.repo_root / "corpora"
        self.policy_dir = self.corpora_dir / "policy"
        self.data_dir = self.repo_root / "data"
        self.manifest_path = self.data_dir / "manifest.json"

    def build_manifest(
        self,
        corpus_version: str = "v1.0",
        embedder_model: str = DEFAULT_EMBEDDER_MODEL,
        embedding_dim: int = DEFAULT_EMBEDDING_DIM,
    ) -> dict[str, Any]:
        """Construct full manifest dictionary."""
        taxonomy = TaxonomyRegistry(
            intents_path=self.repo_root / "taxonomy" / "intents.yaml",
            aliases_path=self.repo_root / "taxonomy" / "aliases.yaml",
        )

        policy_hash = compute_dir_hash(self.policy_dir, "*.md")
        policy_files = [
            p.name for p in sorted(self.policy_dir.glob("*.md")) if not p.name.startswith("_")
        ]

        faq_tags_path = self.corpora_dir / "faq_intent_tags.csv"
        faq_tags_hash = compute_file_hash(faq_tags_path)

        manifest = {
            "corpus_version": corpus_version,
            "taxonomy_version": taxonomy.version,
            "generated_at": datetime.now(UTC).isoformat(),
            "embedder": {
                "model_name": embedder_model,
                "dimension": embedding_dim,
                "prefix_query": DEFAULT_QUERY_PREFIX,
                "prefix_document": DEFAULT_DOC_PREFIX,
            },
            "stores": {
                "policy": {
                    "file_count": len(policy_files),
                    "files": policy_files,
                    "content_hash": policy_hash,
                },
                "faq": {
                    "tags_csv": str(faq_tags_path.relative_to(self.repo_root)),
                    "tags_hash": faq_tags_hash,
                },
            },
            "taxonomy": {
                "intents_count": len(taxonomy.list_all_intents()),
                "policy_required_count": len(taxonomy.list_policy_required_intents()),
            },
        }

        return manifest

    def write_manifest(
        self,
        dest_path: Path | None = None,
        corpus_version: str = "v1.0",
        embedder_model: str = DEFAULT_EMBEDDER_MODEL,
        embedding_dim: int = DEFAULT_EMBEDDING_DIM,
    ) -> Path:
        """Build and write manifest to disk."""
        target = dest_path or self.manifest_path
        target.parent.mkdir(parents=True, exist_ok=True)

        manifest = self.build_manifest(
            corpus_version=corpus_version,
            embedder_model=embedder_model,
            embedding_dim=embedding_dim,
        )

        with open(target, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return target

    def verify_runtime_compatibility(
        self,
        embedder_model: str,
        embedding_dim: int,
        manifest_path: Path | None = None,
    ) -> list[str]:
        """Validate that current runtime embedder config matches manifest metadata."""
        target = manifest_path or self.manifest_path
        if not target.exists():
            return [
                f"Corpus manifest not found at {target}. Run 'make seed' or 'python -m pipeline.manifest'."
            ]

        with open(target, encoding="utf-8") as f:
            data = json.load(f)

        errors: list[str] = []
        embedder_meta = data.get("embedder", {})

        expected_model = embedder_meta.get("model_name")
        expected_dim = embedder_meta.get("dimension")

        if expected_model and embedder_model.lower() != expected_model.lower():
            errors.append(
                f"Embedder model mismatch: runtime is '{embedder_model}', but indexed corpus was built with '{expected_model}'."
            )

        if expected_dim and embedding_dim != expected_dim:
            errors.append(
                f"Embedding dimension mismatch: runtime is {embedding_dim}d, but indexed corpus was built with {expected_dim}d."
            )

        return errors


def main() -> None:
    """CLI to generate manifest."""
    manager = CorpusManifestManager()
    path = manager.write_manifest()
    print(f"✅ Generated corpus manifest at: {path}")


if __name__ == "__main__":
    main()
