from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.core.db import get_db
from app.models.recent_view import RecentView
from app.models.perfume import Perfume
from app.models.user import User
from app.api.deps import get_current_user_id
from app.models.base import uuid_bytes_to_hex
from datetime import datetime

router = APIRouter(tags=["User"])

def _serialize_perfume_for_recent_view(rv: RecentView):
    p = rv.perfume
    if not p:
        return None
        
    return {
        "viewed_at": rv.viewed_at.isoformat() if rv.viewed_at else None,
        "perfume": {
            "id": uuid_bytes_to_hex(p.id),
            "name": p.name,
            "brand_name": p.brand_name,
            "image_url": p.image_url,
            "gender": p.gender,
            "main_accords": p.main_accords,
        }
    }

@router.get("/recent-views")
def get_recent_views(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    uid: User = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):

    if uid is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authentication required for this endpoint"
        )
    
    user_id_to_filter = uid.id 

    recent_views = (
        db.query(RecentView)
        .options(joinedload(RecentView.perfume))
        .filter(RecentView.user_id == user_id_to_filter)
        .order_by(RecentView.viewed_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    results = [rv for rv in [_serialize_perfume_for_recent_view(rv) for rv in recent_views] if rv is not None]

    return results