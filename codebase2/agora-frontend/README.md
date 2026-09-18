# Agora frontend(phần giao diện) · Growup

> Xem [Hướng dẫn thiết lập chung](../README.md) để chạy toàn bộ frontend và backend.

Khung dùng Next.js + React + Ant Design(thư viện giao diện) + Zustand(thư viện quản lý trạng thái).
Nằm trong `codebase2/agora-frontend/`, cùng cấp với `backend/`.

## Chạy tại máy

Yêu cầu Node.js từ 20.9 trở lên.

```powershell
cd codebase2/agora-frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Mở http://localhost:3000.

## Các trang và chức năng

- `/`: landing page(trang giới thiệu), mô tả dự án và luồng sử dụng.
- `/login`: đăng nhập tài khoản giảng viên.
- `/register`: đăng ký tài khoản giảng viên.
- `/join`: học viên nhập mã và tên hiển thị, không cần tài khoản.
- `/dashboard`: trang tổng quan dành cho giảng viên.
- `/users`: đường dẫn cũ, tự chuyển về trang tổng quan.
- Các trang trong không gian làm việc chuyển về đăng nhập nếu không có phiên.
- Chế độ mô phỏng lưu tài khoản giảng viên trong trình duyệt. Mật khẩu được băm bằng
  PBKDF2(cơ chế băm mật khẩu lặp nhiều lần), không lưu nguyên văn.

## Cấu trúc

```text
app/                 Các trang, bố cục và cấu hình dùng chung
components/Layout/   Thanh đầu trang, thanh điều hướng, bố cục bảo vệ trang
components/          Thành phần giao diện dùng chung
services/            Yêu cầu máy chủ và xác thực
stores/              Trạng thái phiên bằng Zustand
hooks/               Hàm useAuth dùng chung
types/               Kiểu dữ liệu
utils/               Hàm tiện ích
public/              Tài nguyên tĩnh
styles/              Kiểu dáng toàn cục
electron/            Điểm khởi chạy ứng dụng máy tính
```

## Nối với backend

Đổi `.env.local`, rồi khởi động lại giao diện:

```dotenv
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_USE_MOCK=false
```

Nếu backend chạy cổng `8001`, dùng:

```dotenv
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001
NEXT_PUBLIC_USE_MOCK=false
```

| Phương thức | Đường dẫn | Yêu cầu / phản hồi |
|---|---|---|
| POST | /auth/login | Nhận email, password; trả `{ user }` và thiết lập cookie |
| POST | /auth/register | Nhận name, email, password; tạo tài khoản giảng viên |
| GET | /auth/me | Trả `{ user }` của phiên hiện tại |
| POST | /auth/logout | Xóa cookie; trả 204 |

Dùng cùng tên máy `localhost` hoặc `127.0.0.1` cho cả hai phía khi dùng cookie.
Không đặt mật khẩu PostgreSQL hoặc khóa AI trong biến có tiền tố `NEXT_PUBLIC_`.

## Kiểm tra và đóng gói

```powershell
npm run typecheck
npm run lint
npm run build
npm run start
```

`package-lock.json` khóa phiên bản thư viện; dùng `npm ci` để cài đúng phiên bản.

## Tài khoản mô phỏng

Khi `NEXT_PUBLIC_USE_MOCK=true`:

```text
Email: teacher@example.com
Mật khẩu: demo123456
```

