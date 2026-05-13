from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, columns, comments, issues, notifications, projects, ws, attachments


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Development mode: auto-create tables.
    # Production: replace this with Alembic migrations.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Jira Clone API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(columns.router)
app.include_router(issues.router)
app.include_router(comments.router)
app.include_router(notifications.router)
app.include_router(attachments.router)
app.include_router(ws.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
