"""Unit-тесты индекса и ответов: без сети, детерминированы."""

import io

import pytest
from PIL import Image

from app.services.answerer import answer
from app.services.index import Index, auto_caption


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (100, 80), (255, 255, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def _seeded() -> Index:
    index = Index()
    index.add_text("pgvector", "IVFFlat suits medium collections.")
    index.add_image("whiteboard", "vector index sketch", _png())
    return index


def test_auto_caption() -> None:
    caption = auto_caption(_png())
    assert caption == "100x80 landscape bright image brightness 1.0"
    with pytest.raises(ValueError):
        auto_caption(b"junk")


def test_search_both_modalities() -> None:
    index = _seeded()
    hits = index.search("vector index collections", top_k=3)
    assert [hit.ref for hit in hits] == ["image-1", "text-1"]
    assert hits[0].score == 2.0
    assert hits[1].score == 1.0


def test_answer_citations() -> None:
    result = answer(_seeded(), "Which index for medium collections?")
    assert "[text-1]" in result.answer
    assert result.citations[0].ref == "text-1"


def test_empty_answer() -> None:
    result = answer(Index(), "anything at all")
    assert result.citations == []
    assert "Nothing relevant" in result.answer


def test_bad_input_rejected() -> None:
    index = Index()
    with pytest.raises(ValueError):
        index.add_text("  ", "content")
    with pytest.raises(ValueError):
        index.search("   ")
