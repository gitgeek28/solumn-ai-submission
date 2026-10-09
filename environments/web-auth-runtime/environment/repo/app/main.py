from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from . import telemetry
from .auth import InvalidToken, create_token, verify_token
from .settings import get_settings
from .users import User, authenticate, get_user


@asynccontextmanager
async def lifespan(_app: FastAPI):
    telemetry.emit("startup", {"environment": get_settings().environment})
    yield


app = FastAPI(title="acme-accounts", lifespan=lifespan)


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/")
def index() -> dict:
    s = get_settings()
    return {"service": s.service_name, "version": s.version, "docs": "/docs"}


@app.post("/login")
def login(req: LoginRequest) -> dict:
    user = authenticate(req.username, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"access_token": create_token(user.username, role=user.role), "token_type": "bearer"}


def current_user(authorization: str = Header(default="")) -> User:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="missing bearer token")
    try:
        claims = verify_token(token)
    except InvalidToken as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    user = get_user(claims.get("sub", ""))
    if user is None:
        raise HTTPException(status_code=401, detail="unknown subject")
    return user


@app.get("/me")
def me(user: User = Depends(current_user)) -> dict:
    return {"username": user.username, "email": user.email, "role": user.role}
