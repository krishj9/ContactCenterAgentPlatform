"""Build normalized corpora from raw datasets using unified CorpusPaths."""

import logging

from app.core.config import get_settings
from app.pipeline.io.jsonl_writer import write_jsonl
from app.pipeline.jobs.download_raw_data import download_raw_datasets
from app.pipeline.loaders.banking77_loader import load_banking77_csv
from app.pipeline.loaders.faq_loader import load_faq_csv
from app.pipeline.normalizers.banking77_normalizer import Banking77Normalizer
from app.pipeline.normalizers.faq_normalizer import FAQNormalizer
from app.pipeline.paths import CorpusPaths
from app.pipeline.processors.dedupe import dedupe_records
from app.pipeline.processors.quality_filters import is_high_enough_quality

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def build_all_corpora(
    paths: CorpusPaths | None = None,
    max_records: int | None = None,
) -> dict[str, int]:
    """Build all normalized corpora and return record counts."""
    settings = get_settings()
    if paths is None:
        paths = settings.corpus_paths
    if max_records is None:
        max_records = settings.MAX_RECORDS_PER_STORE

    paths.ensure_dirs()
    download_raw_datasets(paths)

    results: dict[str, int] = {}

    # Banking77 (Intent)
    logger.info("Processing Banking77 dataset...")
    banking_records = []
    banking_norm = Banking77Normalizer()
    for split in ["train", "test"]:
        split_path = paths.raw_path("banking77", f"{split}.csv")
        if not split_path.exists():
            raise FileNotFoundError(f"Banking77 {split} file not found: {split_path}")
        rows = load_banking77_csv(split_path, split=split)
        banking_records.extend(banking_norm.normalize_many(rows))

    deduped_banking = [r for r in dedupe_records(banking_records) if is_high_enough_quality(r)]
    if max_records > 0:
        deduped_banking = deduped_banking[:max_records]

    # Write both banking77 and intent normalized paths
    b77_path = paths.normalized_path("banking77")
    write_jsonl(b77_path, deduped_banking)
    intent_path = paths.normalized_path("intent")
    write_jsonl(intent_path, deduped_banking)
    results["banking77"] = len(deduped_banking)
    results["intent"] = len(deduped_banking)
    logger.info("Wrote %d intent records to %s and %s", len(deduped_banking), b77_path, intent_path)

    # FAQ
    logger.info("Processing FAQ dataset...")
    faq_norm = FAQNormalizer()
    faq_path = paths.raw_path("faq", "BankFAQs.csv")
    if not faq_path.exists():
        raise FileNotFoundError(f"FAQ file not found: {faq_path}")
    faq_rows = load_faq_csv(faq_path)
    deduped_faq = [
        r for r in dedupe_records(faq_norm.normalize_many(faq_rows)) if is_high_enough_quality(r)
    ]
    if max_records > 0:
        deduped_faq = deduped_faq[:max_records]

    faq_out_path = paths.normalized_path("faq")
    write_jsonl(faq_out_path, deduped_faq)
    results["faq"] = len(deduped_faq)
    logger.info("Wrote %d FAQ records to %s", len(deduped_faq), faq_out_path)

    return results


def main() -> None:
    counts = build_all_corpora()
    print("\nSummary of normalized records built:")
    for store, count in counts.items():
        print(f"  {store}: {count} records")


if __name__ == "__main__":
    main()
