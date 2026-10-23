"""Data Quality: Policy Intent Coverage Assertion (P3.11).

Asserts that 100% of taxonomy intents marked with requires_policy=true
have corresponding active policy chunks in the Policy Store.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pipeline.loaders.policy_loader import load_policy_markdown_files
from pipeline.taxonomy import TaxonomyRegistry

repo_root = Path(__file__).resolve().parent.parent.parent


def assert_policy_coverage(policy_dir: Path | None = None) -> None:
    """Verify 100% intent coverage across authored policies."""
    policy_dir = policy_dir or repo_root / "corpora" / "policy"
    taxonomy = TaxonomyRegistry()
    required_intents = set(taxonomy.list_policy_required_intents())

    if not required_intents:
        raise AssertionError(
            "No intents marked with requires_policy=true in taxonomy/intents.yaml."
        )

    covered_intents: set[str] = set()
    records = list(load_policy_markdown_files(policy_dir))

    for rec in records:
        if rec.get("status") == "active":
            for intent in rec.get("intent_labels", []):
                covered_intents.add(intent)

    missing = required_intents - covered_intents

    if missing:
        msg = f"❌ Policy Coverage Check FAILED: {len(missing)} required intents lack active policy documents:\n"
        for m in sorted(missing):
            msg += f"  - {m}\n"
        raise AssertionError(msg)

    print(
        f"✅ Policy Coverage Check PASSED: 100% ({len(required_intents)}/{len(required_intents)}) of policy-required intents are actively covered."
    )


def main() -> None:
    try:
        assert_policy_coverage()
    except AssertionError as e:
        print(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
