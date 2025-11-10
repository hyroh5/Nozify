# backend/app/api/v1/router.py
from fastapi import APIRouter
from app.api.routes.vision.scan import router as vision_router
from app.api.routes.vision.health import router as vision_health_router
from app.api.routes.health import router as health_router
from app.api.routes.catalog.brands import router as brands_router
from app.api.routes.catalog.perfumes import router as perfumes_router


api_v1 = APIRouter()
api_v1.include_router(health_router)
api_v1.include_router(vision_health_router, prefix="/vision", tags=["Vision"])
api_v1.include_router(vision_router, prefix="/vision", tags=["Vision"])
api_v1.include_router(brands_router, tags=["Catalog"])
api_v1.include_router(perfumes_router, tags=["Catalog"])

api_v1.include_router(brands_router)
api_v1.include_router(perfumes_router)