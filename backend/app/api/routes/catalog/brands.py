from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.brand import Brand

router = APIRouter(prefix="/catalog", tags=["catalog"])

@router.get("/brands")
def list_brands(
    q: str | None = Query(None, min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Brand)
    if q:
        query = query.filter(Brand.name.ilike(f"%{q}%"))
    items = query.order_by(Brand.name.asc()).limit(limit).all()
    return [{"id": b.id, "name": b.name, "logo_url": getattr(b, "logo_url", None)} for b in items]
