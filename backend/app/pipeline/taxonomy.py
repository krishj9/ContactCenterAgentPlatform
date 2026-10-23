"""Re-export taxonomy registry for backend app module namespace."""

from pipeline.taxonomy import IntentDefinition, TaxonomyRegistry

__all__ = ["TaxonomyRegistry", "IntentDefinition"]
