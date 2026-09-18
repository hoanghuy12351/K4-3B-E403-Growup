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

## AI diagnostic API

Khởi chạy API từ thư mục `codebase2/backend`:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Kiểm tra server tại `http://127.0.0.1:8000/health` và Swagger tại
`http://127.0.0.1:8000/docs`. API tạo một câu hỏi qua `POST /api/ai/diagnostic`.
Mode và provider được đọc từ `.env` trên backend, không nhận trong request. Đặt
`AI_MODE=deterministic` để kiểm tra HTTP không cần API key; dùng `AI_MODE=llm`
khi cần kiểm tra provider thật và xác nhận `generation.fallbackUsed` là `false`.

```json
{
  "teachingContext": {
    "title": "Tokenization",
    "text": "A token can be a word, part of a word, or a character.",
    "sourceId": "slide-test"
  },
  "options": {
    "questionCount": 1
  }
}
```

`questionCount` hiện phải là `1`; `mode` và `provider` trong request không được
hỗ trợ và sẽ trả về `422`. API cần evidence pack local trong `data/` khi tạo
diagnostic. Lỗi dataset, cấu hình provider hoặc upstream được trả về dưới dạng
JSON an toàn và không chứa API key, prompt hay traceback.

## Multi-section diagnostic sessions

`GET /api/diagnostic-sessions/lesson-materials` trả danh sách PDF có thể chọn từ `data/`.
`POST /api/diagnostic-sessions` tạo draft session bằng cách chuẩn hóa lesson text hoặc
PDF cục bộ đã chọn, segment theo heading/page boundary, rồi gọi
`generate_diagnostic_check()` đúng một lần cho mỗi section. PDF phải gửi bằng đường dẫn
tương đối bên trong `data/`; server không đọc PDF tùy ý ngoài evidence pack.

Luồng API gồm:

1. `POST /api/diagnostic-sessions` tạo draft để giảng viên review.
2. `POST /api/diagnostic-sessions/{sessionId}/start` mở phiên cho học viên.
3. `GET /api/diagnostic-sessions/{sessionId}` trả câu hỏi student-safe, không có `correct`.
4. `POST /api/diagnostic-sessions/{sessionId}/responses` lưu câu trả lời mới nhất của mỗi học viên cho mỗi câu hỏi.
5. `GET /api/diagnostic-sessions/{sessionId}/summary` trả aggregate evidence và gợi ý không bắt buộc.

Các response được lưu trong memory của process, nên sẽ mất khi server khởi động lại.
`MIN_RESPONSE_COUNT` (mặc định `5`) và `MIN_RESPONSE_COVERAGE` (mặc định `0.30`) là
prototype heuristics. Nếu không đủ coverage, summary trả `insufficient_data`, không kết
luận cả lớp đã hiểu.

Ví dụ tạo phiên bằng LLM đã cấu hình trong `.env`:

```bash
curl -X POST http://127.0.0.1:8000/api/diagnostic-sessions \
  -H "Content-Type: application/json" \
  -d '{
    "lesson": { "materialId": "data/vlearn-pack/slides/d1-slide-hackathon.pdf" },
    "expectedStudents": 30
  }'
```

Lấy `sessionId` từ response, sau đó gọi `/start`, GET student endpoint, gửi từng
`studentId`, `questionId`, `sectionId`, `optionId`, rồi GET `/summary`. Với LLM thật,
đặt `AI_MODE=llm`, provider, key và model trong `.env`; chỉ coi provider hoạt động khi
generation metadata của từng section có `mode: "llm"` và `fallbackUsed: false`.
