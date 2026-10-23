"""Taxonomy Registry and Governance CLI (P3.1).

Loads and validates canonical intent definitions, alias mappings, and policy requirements.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class IntentDefinition:
    """Canonical intent definition in the banking taxonomy."""

    label: str
    display_name: str
    description: str
    parent_category: str
    risk_level: str
    requires_policy: bool
    status: str = "active"


class TaxonomyRegistry:
    """Singleton/loader registry for taxonomy/intents.yaml and taxonomy/aliases.yaml."""

    def __init__(
        self,
        intents_path: Path | str | None = None,
        aliases_path: Path | str | None = None,
    ) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        self.intents_path = Path(intents_path or repo_root / "taxonomy" / "intents.yaml")
        self.aliases_path = Path(aliases_path or repo_root / "taxonomy" / "aliases.yaml")

        self._intents: dict[str, IntentDefinition] = {}
        self._aliases: dict[str, str] = {}
        self._version: str = "unknown"
        self._load()

    def _load(self) -> None:
        """Parse intents and alias dictionaries."""
        if not self.intents_path.exists():
            raise FileNotFoundError(f"Taxonomy intents file not found at {self.intents_path}")

        with open(self.intents_path, encoding="utf-8") as f:
            intents_data = yaml.safe_load(f)

        self._version = intents_data.get("version", "unknown")
        for item in intents_data.get("intents", []):
            defn = IntentDefinition(
                label=item["label"],
                display_name=item["display_name"],
                description=item["description"],
                parent_category=item["parent_category"],
                risk_level=item["risk_level"],
                requires_policy=bool(item.get("requires_policy", False)),
                status=item.get("status", "active"),
            )
            self._intents[defn.label] = defn

        if self.aliases_path.exists():
            with open(self.aliases_path, encoding="utf-8") as f:
                aliases_data = yaml.safe_load(f)

            for canonical, alias_list in aliases_data.get("aliases", {}).items():
                for alias in alias_list:
                    self._aliases[alias.lower().strip()] = canonical

    @property
    def version(self) -> str:
        return self._version

    def get_intent(self, label_or_alias: str) -> IntentDefinition | None:
        """Resolve label or alias and return IntentDefinition."""
        canonical = self.resolve_alias(label_or_alias)
        return self._intents.get(canonical)

    def resolve_alias(self, term: str) -> str:
        """Map term or colloquial alias to canonical taxonomy label."""
        cleaned = term.lower().strip()
        if cleaned in self._aliases:
            return self._aliases[cleaned]
        if cleaned in self._intents:
            return cleaned

        underscored = cleaned.replace(" ", "_").replace("-", "_")
        if underscored in self._aliases:
            return self._aliases[underscored]
        if underscored in self._intents:
            return underscored
        return self._aliases.get(underscored, term)

    def requires_policy(self, label_or_alias: str) -> bool:
        """Check if an intent requires authoritative policy backing (R10, R13)."""
        intent = self.get_intent(label_or_alias)
        if intent is None:
            return False
        return intent.requires_policy

    def list_policy_required_intents(self) -> list[str]:
        """Return list of all canonical labels where requires_policy=True."""
        return [lbl for lbl, defn in self._intents.items() if defn.requires_policy]

    def list_all_intents(self) -> list[IntentDefinition]:
        """Return all registered intent definitions."""
        return list(self._intents.values())

    def validate(self) -> list[str]:
        """Validate taxonomy consistency and return any diagnostic errors."""
        errors: list[str] = []

        if not self._intents:
            errors.append("Taxonomy registry has 0 loaded intents.")

        # Check aliases point to existing canonical intents
        for alias, canonical in self._aliases.items():
            if canonical not in self._intents:
                errors.append(f"Alias '{alias}' references unknown canonical intent '{canonical}'.")

        # Check policy required intents exist
        policy_intents = self.list_policy_required_intents()
        if not policy_intents:
            errors.append("No intents marked with requires_policy=true.")

        return errors


def main() -> None:
    """CLI entrypoint for taxonomy validation."""
    parser = argparse.ArgumentParser(description="Taxonomy Registry CLI")
    parser.add_argument(
        "command", choices=["validate", "list", "check-policy"], help="Action to execute"
    )
    args = parser.parse_args()

    registry = TaxonomyRegistry()

    if args.command == "validate":
        errors = registry.validate()
        if errors:
            print("❌ Taxonomy validation failed:")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        else:
            print(
                f"✅ Taxonomy v{registry.version} valid! ({len(registry.list_all_intents())} intents, {len(registry.list_policy_required_intents())} policy-required)"
            )

    elif args.command == "list":
        print(f"Taxonomy v{registry.version}:")
        for intent in sorted(registry.list_all_intents(), key=lambda x: x.label):
            pol_flag = " [POLICY REQUIRED]" if intent.requires_policy else ""
            print(f"  - {intent.label} ({intent.risk_level} risk){pol_flag}: {intent.display_name}")

    elif args.command == "check-policy":
        policy_intents = registry.list_policy_required_intents()
        print(f"Policy-Required Intents ({len(policy_intents)}):")
        for lbl in sorted(policy_intents):
            print(f"  - {lbl}")


if __name__ == "__main__":
    main()
