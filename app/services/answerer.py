"""Ответы с цитатами по найденным документам."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.services.index import Doc, Index


class Citation(BaseModel):
    ref: str
    title: str


class Answer(BaseModel):
    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)


def answer(index: Index, question: str, top_k: int = 3, min_score: float = 1.0) -> Answer:
    """Собрать ответ из топ-документов. Детерминировано."""
    hits = index.search(question, top_k, min_score)
    by_ref = {doc.ref: doc for doc in index.all_docs()}
    parts: list[str] = []
    citations: list[Citation] = []
    for hit in hits:
        doc: Doc = by_ref[hit.ref]
        snippet = doc.text.split(". ")[0].rstrip(".")
        parts.append(f"{snippet} [{hit.ref}]")
        citations.append(Citation(ref=hit.ref, title=hit.title))
    if not parts:
        return Answer(
            question=question.strip(),
            answer="Nothing relevant in the index yet.",
            citations=[],
        )
    return Answer(question=question.strip(), answer=" ".join(parts) + ".", citations=citations)
