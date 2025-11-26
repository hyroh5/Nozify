from fastapi import APIRouter
from app.api.routes.vision.scan import router as vision_router
from app.api.routes.vision.health import router as vision_health_router
from app.api.routes.health import router as health_router
from app.api.routes.catalog.brands import router as brands_router
from app.api.routes.catalog.perfumes import router as perfumes_router
from app.api.routes.user.recent_views import router as recent_views_router
from app.api.routes.user.wishlist import router as wishlist_router
from app.api.routes.catalog.search import router as search_router
from app.api.routes.catalog.filters import router as filters_router
from app.api.routes import auth as auth_router
from app.api.routes.pbti import router as pbti_router
from app.api.routes.user.purchase_history import router as purchase_history_router
from app.api.routes.catalog.perfumes import router as perfumes_router
from app.api.routes.catalog.seasonal import router as seasonal_router
from app.api.routes.recommendations_today import router as recommendations_today_router
from app.api.routes.recommendations_brand import router as recommendations_brand_router
from app.api.routes.recommendations_trending import router as recommendations_trending_router
from app.api.routes.recommendations_opposite import router as recommendations_opposite_router



api_v1 = APIRouter()
api_v1.include_router(health_router)
api_v1.include_router(vision_health_router, prefix="/vision", tags=["Vision"])
api_v1.include_router(vision_router, prefix="/vision", tags=["Vision"])

# Catalog
api_v1.include_router(brands_router, tags=["Catalog"])
api_v1.include_router(perfumes_router, tags=["Catalog"])
api_v1.include_router(search_router, tags=["Catalog"])
api_v1.include_router(filters_router, tags=["Catalog"])

api_v1.include_router(recent_views_router, prefix="/user", tags=["User"])
api_v1.include_router(wishlist_router, prefix="/user", tags=["User"])
api_v1.include_router(purchase_history_router, prefix="/user", tags=["User"])

# Auth (인증/사용자 관리)
api_v1.include_router(auth_router.router) 

# PBTI
api_v1.include_router(pbti_router, tags=["PBTI"])

api_v1.include_router(perfumes_router, tags=["Catalog"])
api_v1.include_router(seasonal_router, tags=["Seasonal"])
api_v1.include_router(recommendations_today_router)
api_v1.include_router(recommendations_brand_router)
api_v1.include_router(recommendations_trending_router)
api_v1.include_router(recommendations_opposite_router, tags=["Recommendations"])

