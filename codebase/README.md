# Growup — Bản mẫu CP2

Bản đã triển khai: https://hoanghuy12351.github.io/K4-3B-E403-Growup/

Nguồn công khai nằm ở nhánh `codex/cp2-pages` của kho nhóm. GitHub Pages chỉ phục vụ giao diện bản mẫu từ nhánh này.

Mở `index.html` bằng trình duyệt để thử ngay. Bản mẫu không cần cài thêm thư viện hoặc khóa AI.

Nếu muốn xem qua máy chủ cục bộ, từ thư mục gốc dự án chạy:

```powershell
node codebase/server.cjs
```

Sau đó mở `http://127.0.0.1:4173`. Nhấn Ctrl+C trong cửa sổ chạy lệnh để dừng.

Luồng: chọn một hoặc nhiều khái niệm → tạo bản nháp → giảng viên xem/sửa/duyệt từng câu và đáp án → mở kiểm tra → học viên trả lời → giảng viên xem tổng hợp → lưu quyết định.

Nguồn hiện tại là ba đoạn mẫu do nhóm tự soạn. Chưa có nhập tệp hoặc kết nối tài liệu bài học trên VLearn. Khi sửa câu hỏi hoặc phạm vi, phải duyệt lại; không sử dụng phản hồi giả lập của bộ câu cũ cho câu đã sửa.

Chỉ có dữ liệu giả lập và quy tắc đáp án mẫu. Chưa gọi AI, chưa kết nối VLearn, không đồng bộ nhiều thiết bị. Dữ liệu lượt thử chỉ nằm trong bộ nhớ của trang, tải lại sẽ mất.

Chi tiết bài nộp và kịch bản trình diễn nằm trong `../cp2.md`.
