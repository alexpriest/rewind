from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rewind.db import init_db
from rewind.routers import entries, graph, import_router, photos, reports, tags


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Rewind", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(import_router.router)
app.include_router(entries.router)
app.include_router(tags.router)
app.include_router(photos.router)
app.include_router(graph.router)
app.include_router(reports.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
