"""Multi-turn RAG Query Builder (P5.1).

Synthesizes rich search queries from recent customer turns, the detected intent label,
and taxonomy definitions (Spec §3.3.2).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pipeline.taxonomy import TaxonomyRegistry


@dataclass(frozen=True)
class BuiltQuery:
    """Synthesized query payload for hybrid vector + keyword retrieval."""

    query_text: str
    intent_label: str
    intent_description: str
    requires_policy: bool
    customer_turns: list[str]
    filter_labels: list[str] = field(default_factory=list)

    @property
    def sparse_query(self) -> str:
        """Query formatted for sparse/keyword retrieval."""
        return self.query_text


class RAGQueryBuilder:
    """Builds retrieval queries combining conversational turns with taxonomy knowledge."""

    def __init__(self, taxonomy: TaxonomyRegistry | None = None) -> None:
        self.taxonomy = taxonomy or TaxonomyRegistry()

    def build_query(
        self,
        customer_turns: list[str],
        intent_label: str,
        max_turns: int = 3,
    ) -> BuiltQuery:
        """Synthesize retrieval query from last N customer turns + intent label + description."""
        # 1. Normalize intent and resolve aliases
        canonical_label = self.taxonomy.resolve_alias(intent_label)
        intent_def = self.taxonomy.get_intent(canonical_label)

        intent_desc = intent_def.description if intent_def else canonical_label.replace("_", " ")
        requires_policy = intent_def.requires_policy if intent_def else True

        # 2. Extract recent customer dialogue turns (up to max_turns)
        recent_turns = [t.strip() for t in customer_turns if t.strip()][-max_turns:]
        turns_context = " ".join(recent_turns)

        # 3. Formulate dense query according to Spec §3.3.2
        # Combines customer request context with authoritative domain intent description
        if turns_context:
            synthesized_text = f"{turns_context} | Intent: {canonical_label} - {intent_desc}"
        else:
            synthesized_text = f"Intent: {canonical_label} - {intent_desc}"

        return BuiltQuery(
            query_text=synthesized_text,
            intent_label=canonical_label,
            intent_description=intent_desc,
            requires_policy=requires_policy,
            customer_turns=recent_turns,
            filter_labels=[canonical_label],
        )
