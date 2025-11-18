# backend/app/api/routes/catalog/filters.py
from __future__ import annotations
from collections import Counter
from typing import Iterable

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.perfume import Perfume

router = APIRouter(prefix="/catalog", tags=["Catalog"])

def _iter_note_names(perf: Perfume) -> Iterable[str]:
    # general_notes: ["Lemon", ...]
    if perf.general_notes:
        for n in perf.general_notes:
            if isinstance(n, str) and n:
                yield n

    # detailed notes: [{"name": "...", "imageUrl": "..."}, ...]
    def extract(arr):
        if not arr:
            return
        for it in arr:
            if isinstance(it, dict):
                name = it.get("name")
                if name:
                    yield name

    yield from extract(perf.top_notes)
    yield from extract(perf.middle_notes)
    yield from extract(perf.base_notes)

def _iter_accords(perf: Perfume) -> Iterable[str]:
    if perf.main_accords:
        for a in perf.main_accords:
            if isinstance(a, str) and a:
                yield a

@router.get("/notes")
def list_notes(
    q: str | None = Query(None, min_length=1, description="노트명 부분검색"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """저장된 Perfume에서 노트 이름을 수집/집계해서 상위 노트 반환"""
    notes_counter: Counter[str] = Counter()

    for perf in db.query(Perfume.id, Perfume.general_notes, Perfume.top_notes,
                         Perfume.middle_notes, Perfume.base_notes).all():
        # perf는 named tuple 형태(컬럼 선택) -> dict 접근 불가, 필드명 접근
        fake = Perfume()  # 간단히 컨테이너로만 사용
        fake.general_notes = perf.general_notes
        fake.top_notes = perf.top_notes
        fake.middle_notes = perf.middle_notes
        fake.base_notes = perf.base_notes
        for name in _iter_note_names(fake):
            notes_counter[name] += 1

    items = notes_counter.most_common()
    if q:
        q_lower = q.lower()
        items = [it for it in items if q_lower in it[0].lower()]

    items = items[:limit]
    return [
        {"name": name, "occurrence": cnt}
        for name, cnt in items
    ]

@router.get("/accords")
def list_accords(
    q: str | None = Query(None, min_length=1, description="계열명 부분검색"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """저장된 Perfume에서 main_accords를 집계해서 상위 계열 반환"""
    acc_counter: Counter[str] = Counter()

    for perf in db.query(Perfume.id, Perfume.main_accords).all():
        # perf.main_accords 는 ["sweet","floral",...] 형태
        if perf.main_accords:
            for a in perf.main_accords:
                if isinstance(a, str) and a:
                    acc_counter[a] += 1

    items = acc_counter.most_common()
    if q:
        q_lower = q.lower()
        items = [it for it in items if q_lower in it[0].lower()]

    items = items[:limit]
    return [
        {"name": name, "occurrence": cnt}
        for name, cnt in items
    ]

@router.get("/filters/summary")
def filters_summary(
    topk: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """프론트 필터 화면에 쓸 요약치: 상위 accords, 상위 notes"""
    acc_counter: Counter[str] = Counter()
    note_counter: Counter[str] = Counter()

    # 한 번에 필요한 컬럼만 조회
    for perf in db.query(
        Perfume.id, Perfume.main_accords, Perfume.general_notes,
        Perfume.top_notes, Perfume.middle_notes, Perfume.base_notes
    ).all():
        # accords
        if perf.main_accords:
            for a in perf.main_accords:
                if isinstance(a, str) and a:
                    acc_counter[a] += 1

        # notes
        fake = Perfume()
        fake.general_notes = perf.general_notes
        fake.top_notes = perf.top_notes
        fake.middle_notes = perf.middle_notes
        fake.base_notes = perf.base_notes
        for n in _iter_note_names(fake):
            note_counter[n] += 1

    top_accords = [{"name": n, "occurrence": c} for n, c in acc_counter.most_common(topk)]
    top_notes = [{"name": n, "occurrence": c} for n, c in note_counter.most_common(topk)]

    return {
        "top_accords": top_accords,
        "top_notes": top_notes,
    }
