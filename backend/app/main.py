import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers.search import router as search_router

settings = get_settings()

logging.basicConfig(level=settings.log_level)

tags_metadata = [
    {
        "name": "search",
        "description": "Search clinical trials and get type-ahead suggestions",
    },
]

app = FastAPI(
    title="Clinical Trials Search API",
    description="Natural language search for clinical trials",
    version="1.0.0",
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


app.include_router(search_router, prefix="/api", tags=["search"])


@app.get("/health")
def health():
    return {"status": "healthy", "es_url": settings.es_url}


@app.get("/ready")
def ready():
    """Readiness probe that checks Elasticsearch connectivity."""
    from elasticsearch import Elasticsearch

    try:
        es = Elasticsearch([settings.es_url])
        if es.ping():
            return {"status": "ready"}
        return JSONResponse(status_code=503, content={"status": "not ready", "detail": "Elasticsearch not reachable"})
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "not ready", "detail": str(exc)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
