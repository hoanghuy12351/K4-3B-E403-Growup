"""Kiểm thử đăng ký và đăng nhập chỉ dành cho giảng viên."""

import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["FRONTEND_ORIGINS"] = "http://localhost:3000"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_teacher_authentication_flow() -> None:
    with TestClient(app) as client:
        register = client.post("/auth/register", json={
            "name": "Giảng viên thử",
            "email": "teacher-test@example.com",
            "password": "secure-demo-123",
        })
        assert register.status_code == 201
        assert register.json()["user"]["role"] == "teacher"
        assert "growup_session" in register.cookies

        me = client.get("/auth/me")
        assert me.status_code == 200
        assert me.json()["user"]["email"] == "teacher-test@example.com"

        logout = client.post("/auth/logout")
        assert logout.status_code == 204
        assert client.get("/auth/me").status_code == 401

        login = client.post("/auth/login", json={
            "email": "teacher-test@example.com",
            "password": "secure-demo-123",
        })
        assert login.status_code == 200


def test_registration_rejects_student_role_and_duplicate_email() -> None:
    with TestClient(app) as client:
        payload = {
            "name": "Giảng viên khác",
            "email": "duplicate@example.com",
            "password": "secure-demo-456",
        }
        assert client.post("/auth/register", json=payload).status_code == 201
        assert client.post("/auth/register", json=payload).status_code == 409
        assert client.post("/auth/register", json={**payload, "role": "student"}).status_code == 422
