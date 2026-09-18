"""API đăng ký, đăng nhập và đăng xuất dành riêng cho giảng viên."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import Teacher
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.services.user_service import (
    EmailAlreadyExistsError,
    authenticate_teacher,
    create_login_session,
    register_teacher,
    revoke_session,
    teacher_from_session,
)

router = APIRouter(prefix="/auth", tags=["auth"])
DbSession = Annotated[Session, Depends(get_db)]
SessionCookie = Annotated[str | None, Cookie(alias="growup_session")]


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key="growup_session",
        value=token,
        max_age=settings.session_hours * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def current_teacher(db: DbSession, growup_session: SessionCookie = None) -> Teacher:
    teacher = teacher_from_session(db, growup_session)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phiên đăng nhập không hợp lệ.")
    return teacher


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: DbSession) -> AuthResponse:
    try:
        teacher = register_teacher(db, payload)
    except EmailAlreadyExistsError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email này đã có tài khoản giảng viên.") from error
    set_session_cookie(response, create_login_session(db, teacher))
    return AuthResponse(user=teacher)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: DbSession) -> AuthResponse:
    teacher = authenticate_teacher(db, str(payload.email), payload.password)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email hoặc mật khẩu chưa đúng.")
    set_session_cookie(response, create_login_session(db, teacher))
    return AuthResponse(user=teacher)


@router.get("/me", response_model=AuthResponse)
def me(teacher: Annotated[Teacher, Depends(current_teacher)]) -> AuthResponse:
    return AuthResponse(user=teacher)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, db: DbSession, growup_session: SessionCookie = None) -> None:
    revoke_session(db, growup_session)
    response.delete_cookie("growup_session", path="/")
