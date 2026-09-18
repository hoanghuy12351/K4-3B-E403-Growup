# Agora frontend(phần giao diện) · Growup

Khung dùng Next.js + React + Ant Design(thư viện giao diện) + Zustand(thư viện quản lý trạng thái).
Nằm trong `codebase2/agora-frontend/`, cùng cấp với `backend/`.

## Chạy tại máy

Yêu cầu Node.js từ 20.9 trở lên.

```powershell
cd codebase2/agora-frontend
npm install
npm run dev
```

Mở http://localhost:3000. Tệp `.env.local` đã có cấu hình dùng thử.
Máy khác có thể sao chép `.env.example` thành `.env.local`.

## Các trang và chức năng

- `/`: chuyển đến trang tổng quan.
- `/login`: đăng nhập; chế độ mô phỏng nhận email hợp lệ và mật khẩu từ 6 ký tự.
- `/dashboard`: trang tổng quan và khung luồng kiểm tra mức hiểu; chưa có đánh giá AI.
- `/users`: danh sách, tìm kiếm, thêm, sửa, xóa người dùng; chặn email trùng.
- Các trang trong không gian làm việc chuyển về đăng nhập nếu không có phiên.
- Chế độ mô phỏng lưu người dùng và phiên dùng thử trong trình duyệt, không lưu mật khẩu.

Dữ liệu mẫu tự soạn, không lấy từ bộ dữ liệu của ban tổ chức.

## Cấu trúc

```text
app/                 Các trang, bố cục và cấu hình dùng chung
components/Layout/   Thanh đầu trang, thanh điều hướng, bố cục bảo vệ trang
components/          Bảng người dùng, biểu mẫu và trạng thái tải
services/            Yêu cầu máy chủ, đăng nhập và thao tác người dùng
stores/              Trạng thái phiên đăng nhập bằng Zustand
hooks/               Hàm useAuth dùng chung
types/               Kiểu dữ liệu người dùng
utils/               Hàm tiện ích
public/              Tài nguyên tĩnh
styles/              Kiểu dáng toàn cục
electron/            Điểm khởi chạy cửa sổ ứng dụng máy tính
```

## Nối với máy chủ Python

Đổi `.env.local`, rồi khởi động lại giao diện:

```dotenv
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_USE_MOCK=false
```

Các tuyến máy chủ cần triển khai:

| Phương thức | Đường dẫn | Yêu cầu / phản hồi |
|---|---|---|
| POST | /auth/login | Nhận email, password; trả `{ user }` và thiết lập cookie phiên |
| GET | /auth/me | Trả `{ user }` của phiên hiện tại |
| POST | /auth/logout | Xóa cookie phiên; trả 204 |
| GET | /users | Trả mảng người dùng |
| POST | /users | Nhận name, email, role; trả người dùng đã tạo |
| PUT | /users/{id} | Nhận name, email, role; trả người dùng đã sửa |
| DELETE | /users/{id} | Xóa người dùng; trả 204 |

Người dùng có `id, name, email, role`; role nhận `teacher` hoặc `student`.
Máy chủ phải xác thực phiên và kiểm tra quyền cho từng tuyến.
Máy chủ Python hiện mới có khung, chưa triển khai các tuyến trên.

Để dùng cookie giữa hai địa chỉ, cấu hình CORS(cho phép giao tiếp khác nguồn)
với địa chỉ giao diện cụ thể và cho phép gửi thông tin xác thực.
Nên dùng cùng tên máy `localhost` hoặc `127.0.0.1` cho cả hai phía khi nối phiên cookie.
Không đặt mật khẩu PostgreSQL hoặc khóa AI trong biến có tiền tố `NEXT_PUBLIC_`.

## Kiểm tra và đóng gói

```powershell
npm run typecheck
npm run lint
npm run build
npm run start
```

`package-lock.json` khóa phiên bản thư viện; dùng `npm ci` để cài lại đúng phiên bản.

## Cửa sổ ứng dụng máy tính

Chạy `npm run dev` ở cửa sổ lệnh thứ nhất, rồi chạy `npm run desktop`
ở cửa sổ lệnh thứ hai. Electron(khung tạo ứng dụng máy tính) mở giao diện tại
http://localhost:3000; hiện chưa cấu hình gói cài đặt cho ứng dụng máy tính.

## Tài liệu chính thức

- [Next.js: cài đặt](https://nextjs.org/docs/app/getting-started/installation)
- [Ant Design: tích hợp Next.js](https://ant.design/docs/react/use-with-next/)

