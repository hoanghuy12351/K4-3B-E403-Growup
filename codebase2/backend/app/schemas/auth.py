"""Dữ liệu đầu vào và đầu ra cho xác thực giảng viên."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.user import TeacherResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(extra="forbid")


class RegisterRequest(LoginRequest):
    name: str = Field(min_length=2, max_length=100)


class AuthResponse(BaseModel):
    user: TeacherResponse
