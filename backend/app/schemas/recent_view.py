# backend/app/schemas/recent_view.py
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Any, Dict


class RecentViewPerfumeItem(BaseModel):
    id: str
    name: str
    brand_name: Optional[str] = None
    image_url: Optional[str] = None
    gender: Optional[str] = None
    main_accords: Optional[List[str]] = None

    class Config:
        orm_mode = True


class RecentViewItem(BaseModel):
    viewed_at: Optional[datetime] = None
    perfume: RecentViewPerfumeItem

    class Config:
        orm_mode = True
