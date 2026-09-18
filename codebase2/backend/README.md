# Backend(phần xử lý phía máy chủ) · Growup

Cấu trúc mới nằm trong `codebase2/backend/`.
Đây là khung thư mục và tệp, chưa triển khai máy chủ hoặc kết nối cơ sở dữ liệu.
Cơ sở dữ liệu được chọn: PostgreSQL(hệ quản trị cơ sở dữ liệu quan hệ).

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── users.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── user_service.py
│   └── utils/
│       ├── __init__.py
│       └── security.py
├── tests/
│   └── test_users.py
├── .env
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

Các tệp Python hiện chỉ chứa mô tả trách nhiệm. `requirements.txt`, `Dockerfile`
và `docker-compose.yml` là chỗ dành sẵn, chưa có cấu hình thực thi.
Tệp `.env` đã được quy tắc `.gitignore` tại gốc dự án bỏ qua.

Cấu hình mẫu nằm trong `.env.example`; `.env` đã có các biến tương ứng.
Điền thông tin cơ sở dữ liệu thực tế trước khi triển khai kết nối:

| Biến | Ý nghĩa | Giá trị mẫu |
|---|---|---|
| `DB_HOST` | Địa chỉ máy chạy PostgreSQL | `127.0.0.1` |
| `DB_PORT` | Cổng kết nối | `5432` |
| `DB_NAME` | Tên cơ sở dữ liệu | `growup` |
| `DB_USER` | Tài khoản kết nối | `growup` |
| `DB_PASSWORD` | Mật khẩu tài khoản | Để trống trong mẫu |

Các giá trị mẫu chưa tạo cơ sở dữ liệu hoặc tài khoản. Kết nối và việc đọc cấu hình
sẽ được triển khai trong `app/database.py` và `app/config.py`.
