import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from itsdangerous import BadSignature, URLSafeSerializer
from pydantic import BaseModel

load_dotenv(find_dotenv(usecwd=True))

import crud
import database
from routes.ai import router as ai_router
from routes.board import router as board_router

logger = logging.getLogger(__name__)

STATIC_DIR = Path(os.getenv("STATIC_DIR", str(Path(__file__).parent / "static")))
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
if SECRET_KEY == "dev-secret-key":
    logger.warning("Using insecure default SECRET_KEY — set SECRET_KEY env var in production")
_signer = URLSafeSerializer(SECRET_KEY, salt="session")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    async with database.SessionLocal() as db:
        await crud.seed_default_user(db)
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(board_router)
app.include_router(ai_router)


class Credentials(BaseModel):
    username: str
    password: str


def _get_session(request: Request) -> str | None:
    token = request.cookies.get("session")
    if not token:
        return None
    try:
        return _signer.loads(token)
    except BadSignature:
        return None


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/hello")
def hello():
    return {"message": "hello world"}


@app.post("/api/auth/login")
def login(credentials: Credentials, response: Response):
    if credentials.username == "user" and credentials.password == "password":
        token = _signer.dumps(credentials.username)
        response.set_cookie("session", token, httponly=True, samesite="lax")
        return {"ok": True}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"ok": True}


def _requires_auth(full_path: str) -> bool:
    if full_path.startswith("_next/"):
        return False
    if full_path in ("favicon.ico",):
        return False
    return True


def _is_login_page(full_path: str) -> bool:
    return full_path in ("login", "login/")


@app.get("/{full_path:path}")
def serve_frontend(full_path: str, request: Request):
    if _requires_auth(full_path):
        user = _get_session(request)
        if _is_login_page(full_path):
            if user is not None:
                return RedirectResponse("/", status_code=302)
        else:
            if user is None:
                return RedirectResponse("/login", status_code=302)

    static_root = STATIC_DIR.resolve()
    candidate = (STATIC_DIR / full_path).resolve()
    if not str(candidate).startswith(str(static_root)):
        raise HTTPException(status_code=404)

    rel = STATIC_DIR / full_path
    if rel.is_file():
        return FileResponse(rel)
    # Next.js per-page HTML: /login → login/index.html or login.html
    for page in (
        STATIC_DIR / full_path / "index.html",
        STATIC_DIR / f"{full_path}.html",
    ):
        if page.is_file():
            return FileResponse(page)
    return FileResponse(STATIC_DIR / "index.html")
