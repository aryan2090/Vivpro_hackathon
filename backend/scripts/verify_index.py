"""Verify the clinical trials Elasticsearch index.

Runs a suite of queries to confirm mappings, data transformation,
and search functionality work correctly.

Usage:
    cd backend && python -m scripts.verify_index
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elasticsearch import Elasticsearch
from app.config import get_settings

logger = logging.getLogger(__name__)


class IndexVerifier:
    def __init__(self):
        settings = get_settings()
        self.es = Elasticsearch(settings.es_url)
        self.index = settings.es_index
        self.passed = 0
        self.failed = 0

    def check(self, name: str, condition: bool, detail: str = ""):
        if condition:
            self.passed += 1
            logger.info("PASS: %s %s", name, detail)
        else:
            self.failed += 1
            logger.error("FAIL: %s %s", name, detail)

    def verify_document_count(self):
        count = self.es.count(index=self.index)["count"]
        self.check("Document count", count == 1000, f"(got {count})")

    def verify_term_query(self):
        resp = self.es.search(
            index=self.index,
            query={"term": {"phase": "PHASE2"}},
            size=0,
        )
        hits = resp["hits"]["total"]["value"]
        self.check("Term query: phase=PHASE2", hits > 0, f"(got {hits} hits)")

    def verify_nct_id_exact(self):
        resp = self.es.search(
            index=self.index,
            query={"term": {"nct_id": "NCT06890351"}},
        )
        hits = resp["hits"]["total"]["value"]
        self.check("Term query: nct_id exact match", hits == 1, f"(got {hits})")

    def verify_nested_sponsors(self):
        resp = self.es.search(
            index=self.index,
            query={
                "nested": {
                    "path": "sponsors",
                    "query": {"match": {"sponsors.name": "AstraZeneca"}},
                }
            },
            size=0,
        )
        hits = resp["hits"]["total"]["value"]
        self.check("Nested query: sponsor AstraZeneca", hits > 0, f"(got {hits})")

    def verify_nested_facilities(self):
        resp = self.es.search(
            index=self.index,
            query={
                "nested": {
                    "path": "facilities",
                    "query": {"term": {"facilities.country": "United States"}},
                }
            },
            size=0,
        )
        hits = resp["hits"]["total"]["value"]
        self.check("Nested query: US facilities", hits > 0, f"(got {hits})")

    def verify_nested_conditions(self):
        resp = self.es.search(
            index=self.index,
            query={
                "nested": {
                    "path": "conditions",
                    "query": {"match": {"conditions.name": "Asthma"}},
                }
            },
            size=0,
        )
        hits = resp["hits"]["total"]["value"]
        self.check("Nested query: condition Asthma", hits > 0, f"(got {hits})")

    def verify_range_enrollment(self):
        resp = self.es.search(
            index=self.index,
            query={"range": {"enrollment": {"gte": 100}}},
            size=0,
        )
        hits = resp["hits"]["total"]["value"]
        self.check("Range query: enrollment >= 100", hits > 0, f"(got {hits})")

    def verify_range_date(self):
        resp = self.es.search(
            index=self.index,
            query={"range": {"start_date": {"gte": "2025-01-01"}}},
            size=0,
        )
        hits = resp["hits"]["total"]["value"]
        self.check("Range query: start_date >= 2025", hits > 0, f"(got {hits})")

    def verify_full_text_search(self):
        resp = self.es.search(
            index=self.index,
            query={
                "multi_match": {
                    "query": "asthma",
                    "fields": [
                        "brief_title",
                        "official_title",
                        "brief_summaries_description",
                    ],
                }
            },
            size=0,
        )
        hits = resp["hits"]["total"]["value"]
        self.check("Full-text search: asthma", hits > 0, f"(got {hits})")

    def verify_autocomplete(self):
        resp = self.es.search(
            index=self.index,
            query={
                "multi_match": {
                    "query": "Dose",
                    "type": "bool_prefix",
                    "fields": [
                        "brief_title.suggest",
                        "brief_title.suggest._2gram",
                        "brief_title.suggest._3gram",
                    ],
                }
            },
            size=5,
        )
        hits = resp["hits"]["total"]["value"]
        self.check("Autocomplete: 'Dose'", hits > 0, f"(got {hits})")

    def verify_aggregations(self):
        resp = self.es.search(
            index=self.index,
            size=0,
            aggs={
                "phases": {"terms": {"field": "phase", "size": 20}},
                "statuses": {"terms": {"field": "overall_status", "size": 20}},
            },
        )
        phase_buckets = resp["aggregations"]["phases"]["buckets"]
        status_buckets = resp["aggregations"]["statuses"]["buckets"]
        self.check(
            "Aggregation: phase buckets",
            len(phase_buckets) > 0,
            f"(got {len(phase_buckets)} buckets)",
        )
        self.check(
            "Aggregation: status buckets",
            len(status_buckets) > 0,
            f"(got {len(status_buckets)} buckets)",
        )

    def verify_enrollment_nulls(self):
        resp = self.es.search(
            index=self.index,
            query={"bool": {"must_not": {"exists": {"field": "enrollment"}}}},
            size=0,
        )
        null_count = resp["hits"]["total"]["value"]
        self.check(
            "Enrollment null handling",
            null_count > 100,
            f"(got {null_count} null enrollments)",
        )

    def run_all(self) -> bool:
        logger.info("=" * 60)
        logger.info("Verifying index: %s", self.index)
        logger.info("=" * 60)

        self.verify_document_count()
        self.verify_term_query()
        self.verify_nct_id_exact()
        self.verify_nested_sponsors()
        self.verify_nested_facilities()
        self.verify_nested_conditions()
        self.verify_range_enrollment()
        self.verify_range_date()
        self.verify_full_text_search()
        self.verify_autocomplete()
        self.verify_aggregations()
        self.verify_enrollment_nulls()

        logger.info("=" * 60)
        logger.info("Results: %d passed, %d failed", self.passed, self.failed)
        logger.info("=" * 60)

        return self.failed == 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    verifier = IndexVerifier()
    success = verifier.run_all()
    sys.exit(0 if success else 1)
