# backend/app/schemas/purchase_history.py
from datetime import datetime
from pydantic import BaseModel

class PurchaseHistoryItem(BaseModel):
    perfume_id: str
    added_at: datetime
    # purchase_date 제거 → 사용자에게 안 받음

class PurchaseHistoryListResponse(BaseModel):
    items: list[PurchaseHistoryItem]
