from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import auth, crud, imports, dashboard
from .core.config import get_settings
from .db.session import init_db

settings = get_settings()

app = FastAPI(title=settings.app_name)

origins = [o.strip() for o in settings.backend_cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from .api.routes import admin  # lazy import to avoid circular issues
app.include_router(auth.router)
app.include_router(crud.router)
app.include_router(imports.router)
app.include_router(dashboard.router)
app.include_router(admin.router)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def on_startup():
    # For local/dev environments run sync schema to ensure tables exist
    try:
        init_db()
    except Exception:
        # In CI/prod, Alembic handles migrations; ignore failures here
        pass
