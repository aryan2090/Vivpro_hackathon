"""Create the Elasticsearch index for clinical trials data.

Usage:
    cd backend && python -m scripts.create_index
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elasticsearch import Elasticsearch
from app.config import get_settings

logger = logging.getLogger(__name__)

INDEX_SETTINGS = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
        "analyzer": {
            "clinical_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "asciifolding"],
            }
        }
    },
}

INDEX_MAPPINGS = {
    "dynamic": False,
    "properties": {
        # Keyword fields
        "nct_id": {"type": "keyword"},
        "phase": {"type": "keyword"},
        "overall_status": {"type": "keyword"},
        "gender": {"type": "keyword"},
        "study_type": {"type": "keyword"},
        "intervention_model": {"type": "keyword"},
        "primary_purpose": {"type": "keyword"},
        "source": {"type": "keyword"},
        "acronym": {"type": "keyword"},
        "allocation": {"type": "keyword"},
        "masking": {"type": "keyword"},
        "minimum_age": {"type": "keyword"},
        "maximum_age": {"type": "keyword"},
        # Text fields with clinical_analyzer
        "brief_title": {
            "type": "text",
            "analyzer": "clinical_analyzer",
            "fields": {
                "suggest": {"type": "search_as_you_type"},
                "keyword": {"type": "keyword", "ignore_above": 512},
            },
        },
        "official_title": {
            "type": "text",
            "analyzer": "clinical_analyzer",
            "fields": {
                "suggest": {"type": "search_as_you_type"},
                "keyword": {"type": "keyword", "ignore_above": 512},
            },
        },
        "brief_summaries_description": {
            "type": "text",
            "analyzer": "clinical_analyzer",
        },
        "detailed_description": {
            "type": "text",
            "analyzer": "clinical_analyzer",
        },
        # Numeric fields
        "enrollment": {"type": "integer"},
        # Date fields
        "start_date": {"type": "date"},
        "completion_date": {"type": "date"},
        "primary_completion_date": {"type": "date"},
        # Boolean fields
        "healthy_volunteers": {"type": "boolean"},
        "has_results": {"type": "boolean"},
        # Nested: sponsors
        "sponsors": {
            "type": "nested",
            "properties": {
                "name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "agency_class": {"type": "keyword"},
                "lead_or_collaborator": {"type": "keyword"},
            },
        },
        # Nested: facilities
        "facilities": {
            "type": "nested",
            "properties": {
                "name": {"type": "text"},
                "city": {"type": "keyword"},
                "state": {"type": "keyword"},
                "zip": {"type": "keyword"},
                "country": {"type": "keyword"},
                "status": {"type": "keyword"},
            },
        },
        # Nested: design_outcomes
        "design_outcomes": {
            "type": "nested",
            "properties": {
                "outcome_type": {"type": "keyword"},
                "measure": {"type": "text", "analyzer": "clinical_analyzer"},
                "time_frame": {"type": "text"},
                "description": {"type": "text", "analyzer": "clinical_analyzer"},
            },
        },
        # Nested: age
        "age": {
            "type": "nested",
            "properties": {
                "age_category": {"type": "keyword"},
            },
        },
        # Nested: conditions
        "conditions": {
            "type": "nested",
            "properties": {
                "name": {
                    "type": "text",
                    "analyzer": "clinical_analyzer",
                    "fields": {"keyword": {"type": "keyword"}},
                },
            },
        },
        # Nested: interventions
        "interventions": {
            "type": "nested",
            "properties": {
                "intervention_type": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "analyzer": "clinical_analyzer",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "description": {"type": "text", "analyzer": "clinical_analyzer"},
            },
        },
        # Nested: keywords
        "keywords": {
            "type": "nested",
            "properties": {
                "name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
            },
        },
        # Nested: browse_conditions (MeSH terms)
        "browse_conditions": {
            "type": "nested",
            "properties": {
                "mesh_term": {
                    "type": "text",
                    "analyzer": "clinical_analyzer",
                    "fields": {"keyword": {"type": "keyword"}},
                },
            },
        },
        # Nested: browse_interventions (MeSH terms)
        "browse_interventions": {
            "type": "nested",
            "properties": {
                "mesh_term": {
                    "type": "text",
                    "analyzer": "clinical_analyzer",
                    "fields": {"keyword": {"type": "keyword"}},
                },
            },
        },
    },
}


def create_index(delete_existing: bool = True) -> None:
    settings = get_settings()
    es = Elasticsearch(settings.es_url)
    index_name = settings.es_index

    if es.indices.exists(index=index_name):
        if delete_existing:
            logger.info("Deleting existing index '%s'", index_name)
            es.indices.delete(index=index_name)
        else:
            logger.info("Index '%s' already exists, skipping", index_name)
            return

    es.indices.create(
        index=index_name,
        settings=INDEX_SETTINGS,
        mappings=INDEX_MAPPINGS,
    )
    logger.info("Index '%s' created successfully", index_name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    create_index()
