"""Dataset loaders."""

from app.pipeline.loaders.banking77_loader import load_banking77_csv
from app.pipeline.loaders.faq_loader import load_faq_csv

__all__ = ["load_banking77_csv", "load_faq_csv"]
