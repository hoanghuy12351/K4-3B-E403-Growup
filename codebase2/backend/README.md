# Backend(phần xử lý phía máy chủ) · Growup

> Xem [Hướng dẫn thiết lập chung](../README.md) để chạy toàn bộ frontend và backend.

Cấu trúc nằm trong `codebase2/backend/`, dùng FastAPI(khung web Python),
SQLAlchemy(thư viện làm việc với cơ sở dữ liệu) và PostgreSQL(hệ quản trị cơ sở dữ liệu quan hệ).

## Cấu trúc

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   ├── services/
│   └── utils/
├── tests/
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

| Vị trí | Trách nhiệm |
|---|---|
| `app/main.py` | Khởi chạy máy chủ, đăng ký các tuyến |
| `app/config.py` | Đọc cấu hình và biến môi trường |
| `app/database.py` | Kết nối cơ sở dữ liệu |
| `app/models/` | Định nghĩa dữ liệu lưu trữ |
| `app/schemas/` | Kiểm tra cấu trúc dữ liệu yêu cầu và phản hồi |
| `app/routers/` | Nhận yêu cầu và gọi phần xử lý nghiệp vụ |
| `app/services/` | Xử lý nghiệp vụ |
| `app/utils/` | Hàm dùng chung và bảo mật |
| `tests/` | Kiểm thử tự động |

Tệp `.env` được `.gitignore` bỏ qua. Sao chép cấu hình mẫu:

```powershell
Copy-Item .env.example .env
```

| Biến | Ý nghĩa | Giá trị mẫu |
|---|---|---|
| `DB_HOST` | Địa chỉ máy chạy PostgreSQL | `127.0.0.1` |
| `DB_PORT` | Cổng kết nối | `5432` |
| `DB_NAME` | Tên cơ sở dữ liệu | `growup` |
| `DB_USER` | Tài khoản kết nối | `growup` |
| `DB_PASSWORD` | Mật khẩu tài khoản | Để trống trong mẫu |

## Chạy bằng Docker

Mở Docker Desktop rồi chạy:

```powershell
docker compose up --build
```

API chạy tại http://localhost:8000. PostgreSQL chạy trong mạng nội bộ của Docker
và lưu dữ liệu vào volume(kho lưu trữ) riêng.

## Chạy trực tiếp

```powershell
python -m venv .venv
..venvScriptsActivate.ps1
pip install -r requirements.txt
..venvScriptspython.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Điền mật khẩu PostgreSQL trong `.env` trước khi chạy trực tiếp. Nếu cổng `8000`
bị chặn, đổi sang `--port 8001` và cập nhật URL ở frontend.

Kiểm tra:

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

## API tài khoản giảng viên

| Phương thức | Đường dẫn | Mục đích |
|---|---|---|
| `POST` | `/auth/register` | Tạo tài khoản giảng viên và phiên đăng nhập |
| `POST` | `/auth/login` | Xác thực giảng viên |
| `GET` | `/auth/me` | Lấy giảng viên của phiên hiện tại |
| `POST` | `/auth/logout` | Thu hồi phiên và xóa cookie |

Mật khẩu được băm bằng PBKDF2(cơ chế băm mật khẩu lặp nhiều lần). Phiên dùng mã ngẫu nhiên;
cơ sở dữ liệu chỉ lưu giá trị băm của mã. Cookie được đặt `HttpOnly`.
Không có API đăng ký tài khoản học viên; học viên sẽ tham gia lượt kiểm tra bằng mã.

## Kiểm thử

```powershell
..venvScriptspython.exe -m pytest -q -p no:cacheprovider
```

Bộ kiểm thử dùng SQLite(cơ sở dữ liệu gọn trong bộ nhớ); môi trường chạy thật dùng PostgreSQL.

