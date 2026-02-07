"""Ingest clinical trials data into Elasticsearch.

Usage:
    cd backend && python -m scripts.ingest [path/to/clinical_trials.json]
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, BulkIndexError
from app.config import get_settings

logger = logging.getLogger(__name__)

_NONE_STRINGS = {"None", "NA", "N/A", ""}


def _clean_string(value: Any) -> Optional[str]:
    """Convert 'None'/'NA' sentinel strings to None."""
    if value is None:
        return None
    if isinstance(value, str) and value.strip() in _NONE_STRINGS:
        return None
    return str(value)


def _parse_enrollment(value: Any) -> Optional[int]:
    """Convert enrollment string to int. Returns None for invalid values."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned in _NONE_STRINGS:
            return None
        try:
            return int(cleaned)
        except ValueError:
            logger.warning("Invalid enrollment value: %r", value)
            return None
    return None


def _parse_boolean(value: Any) -> Optional[bool]:
    """Convert various boolean representations to bool or None."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower in ("true", "yes", "1"):
            return True
        if lower in ("false", "no", "0"):
            return False
        return None
    return None


def transform_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a raw JSON document for ES indexing."""
    transformed: Dict[str, Any] = {}

    # Keyword fields (clean NA -> None)
    for field in [
        "nct_id", "phase", "overall_status", "gender", "study_type",
        "intervention_model", "primary_purpose", "source", "acronym",
        "allocation", "masking", "minimum_age", "maximum_age",
    ]:
        transformed[field] = _clean_string(doc.get(field))

    # Text fields
    for field in [
        "brief_title", "official_title",
        "brief_summaries_description", "detailed_description",
    ]:
        val = doc.get(field)
        if isinstance(val, str) and val.strip() in _NONE_STRINGS:
            transformed[field] = None
        else:
            transformed[field] = val

    # Enrollment: string -> int
    transformed["enrollment"] = _parse_enrollment(doc.get("enrollment"))

    # Date fields: pass through ISO strings
    for field in ["start_date", "completion_date", "primary_completion_date"]:
        transformed[field] = doc.get(field)

    # Boolean fields
    transformed["healthy_volunteers"] = _parse_boolean(doc.get("healthy_volunteers"))
    transformed["has_results"] = _parse_boolean(doc.get("has_results"))

    # Nested arrays (ensure always list)
    for field in [
        "sponsors", "facilities", "design_outcomes", "age",
        "conditions", "interventions", "keywords",
        "browse_conditions", "browse_interventions",
    ]:
        transformed[field] = doc.get(field) or []

    return transformed


def generate_bulk_actions(
    data: List[Dict], index_name: str
) -> Generator[Dict[str, Any], None, None]:
    """Yield bulk action dicts for elasticsearch.helpers.bulk()."""
    for doc in data:
        transformed = transform_document(doc)
        nct_id = transformed.get("nct_id")
        if not nct_id:
            logger.warning("Skipping document without nct_id")
            continue
        yield {
            "_index": index_name,
            "_id": nct_id,
            "_source": transformed,
        }


def ingest_data(filepath: str) -> None:
    """Load JSON file and bulk-index into Elasticsearch."""
    settings = get_settings()
    es = Elasticsearch(settings.es_url)
    index_name = settings.es_index

    if not es.indices.exists(index=index_name):
        logger.error(
            "Index '%s' does not exist. Run create_index.py first.", index_name
        )
        sys.exit(1)

    logger.info("Loading data from %s", filepath)
    with open(filepath, "r") as f:
        data = json.load(f)
    logger.info("Loaded %d documents", len(data))

    try:
        success, errors = bulk(
            es,
            generate_bulk_actions(data, index_name),
            raise_on_error=False,
            stats_only=False,
        )
        logger.info("Successfully indexed: %d documents", success)
        if errors:
            logger.error("Failed documents: %d", len(errors))
            for err in errors[:10]:
                logger.error("  %s", err)
    except BulkIndexError as e:
        logger.error("Bulk indexing failed: %s", e)
        for err in e.errors[:10]:
            logger.error("  %s", err)
        sys.exit(1)

    es.indices.refresh(index=index_name)
    count = es.count(index=index_name)["count"]
    logger.info("Total documents in index: %d", count)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Ingest clinical trials into ES")
    parser.add_argument(
        "filepath",
        nargs="?",
        default=str(
            Path(__file__).resolve().parent.parent.parent / "clinical_trials.json"
        ),
        help="Path to clinical_trials.json",
    )
    args = parser.parse_args()
    ingest_data(args.filepath)
