"""Эндпоинты индекса и вопросов."""

from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.services.answerer import Answer, answer
from app.services.index import Doc, Index, get_index

router = APIRouter()


class TextDocRequest(BaseModel):
    kind: Literal["text"] = "text"
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1, max_length=20000)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


def get_book() -> Index:
    return get_index()


@router.post("/documents", response_model=Doc)
async def add_text(request: TextDocRequest, book: Index = Depends(get_book)) -> Doc:
    try:
        return book.add_text(request.title, request.content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/images", response_model=Doc)
async def add_image(
    file: UploadFile = File(...),
    title: str = Form(default="untitled"),
    caption: str = Form(default=""),
    book: Index = Depends(get_book),
    settings: Settings = Depends(get_settings),
) -> Doc:
    raw = await file.read()
    if len(raw) > settings.max_image_mb * 1024 * 1024:
        raise HTTPException(status_code=422, detail=f"image exceeds {settings.max_image_mb} MB")
    try:
        return book.add_image(title, caption, raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/documents", response_model=list[Doc])
async def documents(book: Index = Depends(get_book)) -> list[Doc]:
    return book.all_docs()


@router.post("/ask", response_model=Answer)
async def ask(
    request: AskRequest,
    book: Index = Depends(get_book),
    settings: Settings = Depends(get_settings),
) -> Answer:
    try:
        return answer(book, request.question, top_k=settings.top_k, min_score=settings.min_score)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
