"""Các cấu trúc kiểm tra dữ liệu đầu vào và đầu ra."""

from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.user import TeacherResponse

__all__ = ["AuthResponse", "LoginRequest", "RegisterRequest", "TeacherResponse"]
