from fastapi import APIRouter
from app.api.routes.vision.scan import router as vision_router
# (선택) from app.api.routes.catalog.brands import router as brands_router
# (선택) from app.api.routes.catalog.perfumes import router as perfumes_router
# (선택) from app.api.routes.health import router as health_router

api_v1 = APIRouter()
api_v1.include_router(vision_router)
# api_v1.include_router(brands_router, prefix="/catalog")
# api_v1.include_router(perfumes_router, prefix="/catalog")
# api_v1.include_router(health_router)
