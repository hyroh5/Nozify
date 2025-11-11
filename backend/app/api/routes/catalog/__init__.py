from fastapi import APIRouter
from . import brands, perfumes

router = APIRouter(prefix="/catalog", tags=["Catalog"])

router.include_router(brands.router)
router.include_router(perfumes.router)
