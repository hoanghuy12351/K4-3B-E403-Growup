"""Phiên đăng nhập của giảng viên."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import Teacher


class LoginSession(Base):
    __tablename__ = "login_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("teachers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    teacher: Mapped["Teacher"] = relationship(back_populates="sessions")
