"""API-тесты без сети: TestClient."""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from app.services.index import get_index


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (100, 80), (255, 255, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture()
def client() -> TestClient:
    get_index().clear()
    with TestClient(create_app()) as test_client:
        yield test_client
    get_index().clear()


def test_health(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_text_and_image_flow(client: TestClient) -> None:
    text = client.post(
        "/api/v1/documents",
        json={"kind": "text", "title": "pgvector", "content": "IVFFlat suits medium collections."},
    )
    assert text.status_code == 200
    assert text.json()["ref"] == "text-1"
    image = client.post(
        "/api/v1/images",
        files={"file": ("board.png", _png(), "image/png")},
        data={"title": "whiteboard", "caption": "vector index sketch"},
    )
    assert image.status_code == 200
    assert image.json()["ref"] == "image-1"
    asked = client.post("/api/v1/ask", json={"question": "Which index for medium collections?"})
    assert asked.status_code == 200
    assert "[text-1]" in asked.json()["answer"]


def test_ask_empty_index(client: TestClient) -> None:
    resp = client.post("/api/v1/ask", json={"question": "anything"})
    assert resp.status_code == 200
    assert resp.json()["citations"] == []


@pytest.mark.integration()
def test_documents_shape(client: TestClient) -> None:
    """Интеграционный по маркеру: список документов, без сети."""
    client.post("/api/v1/documents", json={"kind": "text", "title": "t", "content": "vector stuff"})
    resp = client.get("/api/v1/documents")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
