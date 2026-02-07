import json
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def clinical_trials_data():
    data_path = Path(__file__).parent.parent.parent / "clinical_trials.json"
    with open(data_path) as f:
        return json.load(f)


@pytest.fixture
def sample_trial(clinical_trials_data):
    return clinical_trials_data[0]


@pytest.fixture
def sample_trial_minimal():
    return {
        "nct_id": "NCT00000001",
        "brief_title": "A Minimal Test Trial",
    }
