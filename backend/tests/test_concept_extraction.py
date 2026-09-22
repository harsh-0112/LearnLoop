import json

import pytest

from app.services import concept_extraction
from app.services.concept_extraction import ConceptExtractionError, extract_concepts_from_text
from tests.factories import FakeAnthropic

VALID_PAYLOAD = {
    "concepts": [
        {
            "name": "Newtons Second Law",
            "description": "Force equals mass times acceleration.",
            "difficulty_level": 3,
            "prerequisites": ["Acceleration"],
        },
        {
            "name": "Acceleration",
            "description": "Rate of change of velocity.",
            "difficulty_level": 2,
            "prerequisites": [],
        },
    ]
}


@pytest.fixture
def fake_client(monkeypatch):
    def _install(responses: list[str]) -> FakeAnthropic:
        client = FakeAnthropic(responses=responses)
        monkeypatch.setattr(concept_extraction, "_get_client", lambda: client)
        return client

    return _install


def test_parses_json_wrapped_in_code_fences(fake_client):
    client = fake_client(["```json\n" + json.dumps(VALID_PAYLOAD) + "\n```"])

    concepts = extract_concepts_from_text("Some physics notes.", "Physics")

    assert [concept["name"] for concept in concepts] == [
        "Newtons Second Law",
        "Acceleration",
    ]
    assert concepts[0]["prerequisites"] == ["Acceleration"]
    assert len(client.messages.calls) == 1


def test_retries_once_when_first_response_is_malformed(fake_client):
    client = fake_client(["not json at all {", json.dumps(VALID_PAYLOAD)])

    concepts = extract_concepts_from_text("Some physics notes.", "Physics")

    assert len(concepts) == 2
    assert len(client.messages.calls) == 2
    retry_messages = client.messages.calls[1]["messages"]
    assert retry_messages[-1]["role"] == "user"
    assert "valid JSON" in retry_messages[-1]["content"]


def test_raises_after_two_malformed_responses(fake_client):
    client = fake_client(["<html>error</html>", "still not json"])

    with pytest.raises(ConceptExtractionError):
        extract_concepts_from_text("Some physics notes.", "Physics")

    assert len(client.messages.calls) == 2


def test_normalizes_out_of_range_difficulty_and_unknown_prerequisites(fake_client):
    fake_client(
        [
            json.dumps(
                {
                    "concepts": [
                        {
                            "name": "Torque",
                            "description": "Rotational force.",
                            "difficulty_level": 99,
                            "prerequisites": ["Nonexistent Concept", "Torque"],
                        },
                        {"name": "  ", "description": "blank name is dropped"},
                    ]
                }
            )
        ]
    )

    concepts = extract_concepts_from_text("notes", "Physics")

    assert len(concepts) == 1
    assert concepts[0]["difficulty_level"] == 5
    assert concepts[0]["prerequisites"] == []


def test_rejects_empty_text(fake_client):
    fake_client([json.dumps(VALID_PAYLOAD)])

    with pytest.raises(ConceptExtractionError):
        extract_concepts_from_text("   ", "Physics")
