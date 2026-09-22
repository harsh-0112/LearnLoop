import json

from sqlalchemy import select

from app.models import Concept, ConceptPrerequisite
from app.services import concept_extraction
from tests.factories import FakeAnthropic

PAYLOAD = {
    "concepts": [
        {
            "name": "Vectors",
            "description": "Quantities with magnitude and direction.",
            "difficulty_level": 2,
            "prerequisites": [],
        },
        {
            "name": "Projectile Motion",
            "description": "Two-dimensional motion under gravity.",
            "difficulty_level": 4,
            "prerequisites": ["Vectors"],
        },
    ]
}


def _install_fake_client(monkeypatch, responses: list[str]) -> FakeAnthropic:
    client = FakeAnthropic(responses=responses)
    monkeypatch.setattr(concept_extraction, "_get_client", lambda: client)
    return client


def test_upload_extracts_and_persists_concepts(client, db_session, monkeypatch):
    _install_fake_client(monkeypatch, [json.dumps(PAYLOAD)])

    response = client.post(
        "/concepts/extract",
        data={"subject": "Physics"},
        files={"file": ("notes.txt", b"Projectiles follow parabolic paths.", "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["created_count"] == 2
    assert body["prerequisite_edge_count"] == 1
    assert {concept["name"] for concept in body["concepts"]} == {"Vectors", "Projectile Motion"}

    stored = db_session.scalars(select(Concept).where(Concept.subject == "Physics")).all()
    assert {concept.name for concept in stored} == {"Vectors", "Projectile Motion"}

    edges = db_session.scalars(select(ConceptPrerequisite)).all()
    by_id = {concept.id: concept.name for concept in stored}
    assert [(by_id[edge.concept_id], by_id[edge.prerequisite_concept_id]) for edge in edges] == [
        ("Projectile Motion", "Vectors")
    ]


def test_second_upload_deduplicates_by_name_within_subject(client, db_session, monkeypatch):
    _install_fake_client(monkeypatch, [json.dumps(PAYLOAD)])
    client.post(
        "/concepts/extract",
        data={"subject": "Physics"},
        files={"file": ("notes.txt", b"first upload", "text/plain")},
    )

    _install_fake_client(
        monkeypatch,
        [
            json.dumps(
                {
                    "concepts": [
                        {"name": "vectors", "description": "dup", "difficulty_level": 2},
                        {"name": "Momentum", "description": "mass times velocity",
                         "difficulty_level": 3, "prerequisites": ["vectors"]},
                    ]
                }
            )
        ],
    )
    response = client.post(
        "/concepts/extract",
        data={"subject": "Physics"},
        files={"file": ("notes2.txt", b"second upload", "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["created_count"] == 1
    assert body["reused_count"] == 1

    names = db_session.scalars(select(Concept.name).where(Concept.subject == "Physics")).all()
    assert sorted(names) == ["Momentum", "Projectile Motion", "Vectors"]


def test_malformed_model_output_returns_502_without_crashing(client, db_session, monkeypatch):
    _install_fake_client(monkeypatch, ["I'm afraid I can't do that", "still prose"])

    response = client.post(
        "/concepts/extract",
        data={"subject": "Physics"},
        files={"file": ("notes.txt", b"some text", "text/plain")},
    )

    assert response.status_code == 502
    assert "concept extraction failed" in response.json()["detail"]
    assert db_session.scalars(select(Concept)).all() == []


def test_empty_upload_is_rejected(client, monkeypatch):
    _install_fake_client(monkeypatch, ["{}"])

    response = client.post(
        "/concepts/extract",
        data={"subject": "Physics"},
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 400


def test_binary_upload_is_rejected_as_unsupported(client, monkeypatch):
    _install_fake_client(monkeypatch, ["{}"])

    response = client.post(
        "/concepts/extract",
        data={"subject": "Physics"},
        files={"file": ("image.png", b"\x89PNG\r\n\x1a\n\xff\xfe\x00", "image/png")},
    )

    assert response.status_code in (400, 415)
