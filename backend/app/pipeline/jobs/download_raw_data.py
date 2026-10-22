"""Download raw dataset files (Banking77 and BankFAQs) if missing."""

import logging
import urllib.request

from app.core.config import get_settings
from app.pipeline.paths import CorpusPaths

logger = logging.getLogger(__name__)

RAW_SOURCES = {
    (
        "banking77",
        "train.csv",
    ): "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/train.csv",
    (
        "banking77",
        "test.csv",
    ): "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/test.csv",
    (
        "faq",
        "BankFAQs.csv",
    ): "https://raw.githubusercontent.com/MrJay10/banking-faq-bot/master/BankFAQs.csv",
}


def download_raw_datasets(paths: CorpusPaths | None = None) -> None:
    """Download raw datasets to the configured raw data directory."""
    if paths is None:
        paths = get_settings().corpus_paths

    paths.ensure_dirs()

    for (store, filename), url in RAW_SOURCES.items():
        dest = paths.raw_path(store, filename)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            logger.info("Downloading %s to %s...", url, dest)
            print(f"Downloading {filename} from {url}...")
            urllib.request.urlretrieve(url, dest)
            print(f"  Saved to {dest} ({dest.stat().st_size} bytes)")
        else:
            logger.info("%s already exists at %s", filename, dest)


if __name__ == "__main__":
    download_raw_datasets()
