from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
import asyncio
from redis.asyncio import Redis as AsyncRedis
import json
from app.core.websocket_manager import manager

from app.core.config import settings
from app.api.routes import auth, users, admin, applications,ws
import logging
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — runs before the server starts accepting requests
    asyncio.create_task(redis_subscriber())
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Document Processing & Verification Platform",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI available at http://localhost:8000/docs
    redoc_url="/redoc",
    lifespan=lifespan       # ReDoc UI available at http://localhost:8000/redoc
)

# CORS tells the browser — "it's okay for requests from this origin to talk to this server"
# Without this, your React app on localhost:5173 cannot call this backend on localhost:8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",
    ],                                       # only allow your frontend URL
    allow_credentials=True,                  # allow cookies and auth headers
    allow_methods=["*"],                     # allow GET, POST, PUT, DELETE etc.
    allow_headers=["*"],                     # allow Authorization header etc.
)




async def redis_subscriber():
    """
    Subscribes to the Redis pub/sub channel that Celery workers publish to.
    Runs forever as a background task. When a message arrives, broadcasts
    it to all connected admin WebSocket clients via the manager.
    """
    redis = await AsyncRedis.from_url(
    settings.REDIS_URL,
    decode_responses=True
    
    )
    pubsub = redis.pubsub()
    await pubsub.subscribe("intelliverify:admin_updates")

    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                await manager.broadcast(data)
            except Exception as e:
                print(f"[Redis Subscriber] Error broadcasting: {e}")


# Hook into FastAPI lifespan events — add to your existing app startup



@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )
# Each router is mounted with a prefix
# All routes inside auth.py become /auth/...
# All routes inside users.py become /users/...
# All routes inside admin.py become /admin/...
# All routes inside applications.py become /applications/...

app.include_router(auth.router,         prefix="/auth",         tags=["Auth"])
app.include_router(users.router,        prefix="/users",        tags=["Users"])
app.include_router(admin.router)
app.include_router(applications.router)
app.include_router(ws.router)


@app.get("/", tags=["Health"])
def root():
    """
    Basic health check.
    Hit http://localhost:8000/ to confirm the server is running.
    """
    return {
        "status": "running",
        "app": settings.APP_NAME,
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    More detailed health check.
    Later we'll add DB connection status and ML service status here.
    """
    return {
        "status": "healthy",
        "debug": settings.DEBUG,
    }

