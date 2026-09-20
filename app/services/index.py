"""Единый индекс текстов и картинок. Без сети."""

from __future__ import annotations

import io
import re

from PIL import Image, ImageStat
from pydantic import BaseModel

_WORD_RE = re.compile(r"[a-zA-Z]+")


class Doc(BaseModel):
    ref: str
    kind: str
    title: str
    text: str


class ScoredDoc(BaseModel):
    ref: str
    kind: str
    title: str
    score: float


def auto_caption(raw: bytes) -> str:
    """Автопризнаки картинки текстом: размер, яркость. Детерминировано."""
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except Exception as exc:
        raise ValueError(f"cannot decode image: {exc}") from exc
    width, height = image.size
    brightness = round(ImageStat.Stat(image.convert("L")).mean[0] / 255.0, 2)
    tone = "bright" if brightness >= 0.5 else "dark"
    orientation = "landscape" if width > height else "portrait" if height > width else "square"
    return f"{width}x{height} {orientation} {tone} image brightness {brightness}"


class Index:
    """Хранилище документов обеих модальностей."""

    def __init__(self) -> None:
        self._docs: list[Doc] = []
        self._counters = {"text": 0, "image": 0}

    def add_text(self, title: str, content: str) -> Doc:
        if not title.strip() or not content.strip():
            raise ValueError("title and content must not be empty")
        self._counters["text"] += 1
        doc = Doc(
            ref=f"text-{self._counters['text']}",
            kind="text",
            title=title.strip(),
            text=content.strip(),
        )
        self._docs.append(doc)
        return doc

    def add_image(self, title: str, caption: str, raw: bytes) -> Doc:
        if not title.strip():
            raise ValueError("title must not be empty")
        auto = auto_caption(raw)
        text = f"{caption.strip()} {auto}".strip()
        self._counters["image"] += 1
        doc = Doc(ref=f"image-{self._counters['image']}", kind="image", title=title.strip(), text=text)
        self._docs.append(doc)
        return doc

    def all_docs(self) -> list[Doc]:
        return list(self._docs)

    def search(self, query: str, top_k: int = 3, min_score: float = 1.0) -> list[ScoredDoc]:
        """Keyword-поиск по заголовку и тексту."""
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        terms = set(_WORD_RE.findall(query.lower()))
        scored: list[ScoredDoc] = []
        for doc in self._docs:
            title_hits = len(terms & set(_WORD_RE.findall(doc.title.lower())))
            text_hits = len(terms & set(_WORD_RE.findall(doc.text.lower())))
            score = round(title_hits * 2.0 + text_hits * 1.0, 2)
            if score >= min_score:
                scored.append(ScoredDoc(ref=doc.ref, kind=doc.kind, title=doc.title, score=score))
        scored.sort(key=lambda item: (-item.score, item.ref))
        return scored[: max(top_k, 0)]

    def clear(self) -> None:
        self._docs.clear()
        self._counters = {"text": 0, "image": 0}


_index: Index | None = None


def get_index() -> Index:
    global _index
    if _index is None:
        _index = Index()
    return _index
