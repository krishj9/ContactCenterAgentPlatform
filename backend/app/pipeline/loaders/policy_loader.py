"""Policy corpus Markdown loader (P3.4).

Loads and validates authored policy Markdown documents with YAML frontmatter from corpora/policy/*.md.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml

from app.pipeline.schemas.raw_record_types import PolicyRawRecord

REQUIRED_FRONTMATTER_FIELDS = [
    "policy_id",
    "version",
    "title",
    "intent_labels",
    "risk_level",
    "owner",
    "effective_from",
    "status",
]

VALID_RISK_LEVELS = {"low", "medium", "high"}
VALID_STATUSES = {"active", "superseded", "retired"}
POLICY_ID_REGEX = re.compile(r"^POL-[A-Z0-9_-]+$")
VERSION_REGEX = re.compile(r"^v[0-9]+(\.[0-9]+)*$")
DATE_REGEX = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def validate_policy_frontmatter(fm: dict[str, Any], filepath: Path) -> list[str]:
    """Validate policy frontmatter against governance schema rules."""
    errors: list[str] = []
    for req in REQUIRED_FRONTMATTER_FIELDS:
        if req not in fm or fm[req] is None or fm[req] == "":
            errors.append(f"Missing required frontmatter field '{req}' in {filepath.name}")

    if "policy_id" in fm and not POLICY_ID_REGEX.match(str(fm["policy_id"])):
        errors.append(f"Invalid policy_id format: '{fm['policy_id']}' in {filepath.name}")

    if "version" in fm and not VERSION_REGEX.match(str(fm["version"])):
        errors.append(f"Invalid version format: '{fm['version']}' in {filepath.name}")

    if "intent_labels" in fm:
        if not isinstance(fm["intent_labels"], list) or len(fm["intent_labels"]) == 0:
            errors.append(f"'intent_labels' must be non-empty list in {filepath.name}")

    if "risk_level" in fm and fm["risk_level"] not in VALID_RISK_LEVELS:
        errors.append(f"Invalid risk_level '{fm['risk_level']}' in {filepath.name}")

    if "status" in fm and fm["status"] not in VALID_STATUSES:
        errors.append(f"Invalid status '{fm['status']}' in {filepath.name}")

    if "effective_from" in fm and not DATE_REGEX.match(str(fm["effective_from"])):
        errors.append(
            f"Invalid effective_from date format: '{fm['effective_from']}' in {filepath.name}"
        )

    return errors


def load_policy_markdown_files(policy_dir: str | Path) -> Iterator[PolicyRawRecord]:
    """Load and validate all Markdown policies in directory."""
    policy_dir = Path(policy_dir)
    if not policy_dir.exists():
        raise FileNotFoundError(f"Policy directory not found: {policy_dir}")

    for file_path in sorted(policy_dir.glob("*.md")):
        if file_path.name.startswith("_"):
            continue

        with open(file_path, encoding="utf-8") as f:
            raw_content = f.read()

        parts = raw_content.split("---", 2)
        if len(parts) < 3:
            raise ValueError(
                f"Malformed policy Markdown (missing YAML frontmatter delimiters): {file_path}"
            )

        frontmatter_raw = parts[1]
        body = parts[2].strip()

        fm_data = yaml.safe_load(frontmatter_raw) or {}
        errors = validate_policy_frontmatter(fm_data, file_path)
        if errors:
            raise ValueError(f"Policy validation failed for {file_path.name}: {'; '.join(errors)}")

        yield {
            "policy_id": str(fm_data["policy_id"]),
            "version": str(fm_data["version"]),
            "title": str(fm_data["title"]),
            "intent_labels": list(fm_data.get("intent_labels", [])),
            "risk_level": str(fm_data["risk_level"]),
            "owner": str(fm_data["owner"]),
            "effective_from": str(fm_data["effective_from"]),
            "effective_to": str(fm_data.get("effective_to"))
            if fm_data.get("effective_to")
            else None,
            "status": str(fm_data["status"]),
            "content": body,
            "file_path": str(file_path),
        }
