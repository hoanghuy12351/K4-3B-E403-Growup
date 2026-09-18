"""Dữ liệu phản hồi của tài khoản giảng viên."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr


class TeacherResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Literal["teacher"] = "teacher"

    model_config = ConfigDict(from_attributes=True)
