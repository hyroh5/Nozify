import requests
from app.core.db import SessionLocal
from app.models import Brand, Perfume

BASE_URL = "https://api.fragella.com/api/v1"

def sync_brands():
    db = SessionLocal()
    url = f"{BASE_URL}/brands"
    res = requests.get(url)
    data = res.json()

    for b in data:
        if not db.query(Brand).filter(Brand.name == b["name"]).first():
            db.add(Brand(id=b["id"], name=b["name"]))
    db.commit()
    db.close()

def sync_perfumes():
    db = SessionLocal()
    url = f"{BASE_URL}/perfumes"
    res = requests.get(url)
    data = res.json()

    for p in data:
        if not db.query(Perfume).filter(Perfume.id == p["id"]).first():
            db.add(
                Perfume(
                    id=p["id"],
                    name=p["name"],
                    brand_id=p["brand"]["id"],
                    image_url=p["image_url"],
                    price=p.get("price")
                )
            )
    db.commit()
    db.close()
