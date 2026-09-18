# Growup · Hướng dẫn thiết lập cho thành viên

Dự án gồm:

- `agora-frontend/`: Next.js(giao diện web) dành cho giảng viên và học viên.
- `backend/`: FastAPI(máy chủ API) và PostgreSQL(cơ sở dữ liệu).

## 1. Yêu cầu

Cài đặt các công cụ sau:

- Git.
- Node.js 20.9 trở lên.
- Python 3.11 trở lên.
- Docker Desktop nếu không cài PostgreSQL trực tiếp.

Kiểm tra:

```powershell
git --version
node --version
npm --version
python --version
docker --version
```

## 2. Lấy mã nguồn

```powershell
git clone https://github.com/hoanghuy12351/K4-3B-E403-Growup.git
cd K4-3B-E403-Growupcodebase2
```

Nếu đã clone:

```powershell
git checkout main
git pull origin main
```

Không commit các tệp `.env`, `.env.local`, `.venv`, `node_modules` hoặc dữ liệu PostgreSQL.

## 3. Chạy backend bằng Docker

Cách này không yêu cầu cài PostgreSQL trực tiếp.

Mở Docker Desktop, sau đó:

```powershell
cd backend
Copy-Item .env.example .env
docker compose up --build
```

Kiểm tra:

- Health check(kiểm tra hoạt động): http://127.0.0.1:8000/health
- Swagger(tài liệu API tương tác): http://127.0.0.1:8000/docs

Dừng dịch vụ:

```powershell
docker compose down
```

Dữ liệu PostgreSQL được giữ trong Docker volume(vùng lưu trữ bền vững). Chỉ dùng
`docker compose down -v` khi chủ động muốn xóa toàn bộ dữ liệu local(máy cá nhân).

## 4. Chạy backend trực tiếp

Dùng cách này khi PostgreSQL đã được cài và đang hoạt động.

```powershell
cd backend
Copy-Item .env.example .env
python -m venv .venv
..venvScriptsActivate.ps1
pip install -r requirements.txt
```

Điền đúng thông tin PostgreSQL trong `.env`:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=growup
DB_USER=growup
DB_PASSWORD=mat_khau_cua_ban
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
SESSION_HOURS=12
COOKIE_SECURE=false
```

Khởi chạy:

```powershell
..venvScriptspython.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Nếu cổng `8000` bị Windows chặn, dùng cổng `8001`:

```powershell
..venvScriptspython.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## 5. Chạy frontend

Mở cửa sổ PowerShell khác:

```powershell
cd agora-frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Mở http://localhost:3000.

Mặc định frontend chạy mock mode(chế độ dữ liệu mô phỏng):

```dotenv
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_USE_MOCK=true
```

Để sử dụng backend thật:

```dotenv
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_USE_MOCK=false
```

Nếu backend chạy ở cổng `8001`, đổi `NEXT_PUBLIC_API_URL` sang:

```dotenv
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001
```

Sau khi sửa `.env.local`, phải dừng và chạy lại `npm run dev`.

## 6. Kiểm thử trước khi đẩy mã

Backend:

```powershell
cd backend
..venvScriptspython.exe -m pytest -q -p no:cacheprovider
```

Frontend:

```powershell
cd agora-frontend
npm run typecheck
npm run lint
npm run build
```

## 7. Tài khoản dùng thử

Khi `NEXT_PUBLIC_USE_MOCK=true`:

```text
Email: teacher@example.com
Mật khẩu: demo123456
```

Chỉ dùng tài khoản này cho môi trường phát triển, không dùng mật khẩu thật.

## 8. Lỗi thường gặp

### PowerShell không cho kích hoạt virtual environment

```powershell
Set-ExecutionPolicy -Scope Process Bypass
..venvScriptsActivate.ps1
```

Hoặc chạy Python trong `.venv` trực tiếp mà không kích hoạt:

```powershell
..venvScriptspython.exe -m uvicorn app.main:app --reload
```

### Không kết nối được PostgreSQL

- Kiểm tra PostgreSQL hoặc Docker Desktop đang chạy.
- Kiểm tra `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` và `DB_PASSWORD`.
- Khi backend chạy trong Docker, database host(tên máy cơ sở dữ liệu) là `db`.
- Khi backend chạy trực tiếp trên Windows, database host là `127.0.0.1`.

### Đăng nhập thành công nhưng frontend không giữ phiên

Dùng cùng một kiểu địa chỉ cho hai phía:

```text
Frontend: http://127.0.0.1:3000
Backend:  http://127.0.0.1:8000
```

Không trộn `localhost` với `127.0.0.1` vì cookie(phiên trình duyệt) có thể không được gửi đúng.

## 9. Quy trình làm việc nhóm

Trước khi bắt đầu:

```powershell
git checkout main
git pull origin main
git checkout -b ten-thanh-vien/tinh-nang
```

Trước khi commit:

```powershell
git status
git diff
```

Chỉ thêm các tệp mã nguồn cần thiết. Không dùng `git add .` nếu chưa kiểm tra danh sách tệp.

