# backend/app/schemas/wishlist.py
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class WishlistPerfumeItem(BaseModel):
    id: str
    name: str
    brand_name: Optional[str] = None
    image_url: Optional[str] = None
    gender: Optional[str] = None

    class Config:
        orm_mode = True


class WishlistItem(BaseModel):
    added_at: Optional[datetime] = None
    perfume: WishlistPerfumeItem

    class Config:
        orm_mode = True


class WishlistCreateRequest(BaseModel):
    perfume_id: str
