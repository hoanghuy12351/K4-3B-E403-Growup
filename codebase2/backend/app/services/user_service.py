"""Nghiệp vụ tài khoản và phiên đăng nhập của giảng viên."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.session import LoginSession
from app.models.user import Teacher
from app.schemas.auth import RegisterRequest
from app.utils.security import (
    create_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)


class EmailAlreadyExistsError(ValueError):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_teacher(db: Session, payload: RegisterRequest) -> Teacher:
    teacher = Teacher(
        name=payload.name.strip(),
        email=normalize_email(str(payload.email)),
        password_hash=hash_password(payload.password),
    )
    db.add(teacher)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise EmailAlreadyExistsError from error
    db.refresh(teacher)
    return teacher


def authenticate_teacher(db: Session, email: str, password: str) -> Teacher | None:
    teacher = db.scalar(select(Teacher).where(Teacher.email == normalize_email(email)))
    if not teacher or not verify_password(password, teacher.password_hash):
        return None
    return teacher


def create_login_session(db: Session, teacher: Teacher) -> str:
    token = create_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=get_settings().session_hours)
    db.add(LoginSession(token_hash=hash_session_token(token), teacher_id=teacher.id, expires_at=expires_at))
    db.commit()
    return token


def teacher_from_session(db: Session, token: str | None) -> Teacher | None:
    if not token:
        return None
    login_session = db.scalar(
        select(LoginSession).where(LoginSession.token_hash == hash_session_token(token))
    )
    if not login_session:
        return None
    expires_at = login_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        db.delete(login_session)
        db.commit()
        return None
    return login_session.teacher


def revoke_session(db: Session, token: str | None) -> None:
    if not token:
        return
    db.execute(delete(LoginSession).where(LoginSession.token_hash == hash_session_token(token)))
    db.commit()
