from fastapi import FastAPI
from app.api.routes.vision.health import router as health_router
from app.api.routes.vision.scan import router as scan_router

app = FastAPI()
app.include_router(health_router)
app.include_router(scan_router)