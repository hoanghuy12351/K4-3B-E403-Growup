# Bằng chứng CP4 — nhu cầu kiểm tra mức hiểu của lớp

## Câu hỏi phân tích

Trong dữ liệu VLearn của chính khóa K4, có bao nhiêu học viên chủ động yêu cầu
giải thích hoặc làm rõ kiến thức, và dữ liệu hiện tại có đủ tín hiệu để giảng viên
biết mức hiểu của lớp hay không?

## Nguồn và phạm vi

- Nguồn: `data/vlearn-pack/chatlog/tutor_turns.csv`, bản xuất ngày 15/09/2026.
- Chỉ lấy các dòng `cohort_hint = K4`.
- Tổng: **3.097 lượt hỏi–đáp của 448 học viên**.
- Loại câu mẫu bằng điều kiện `is_preset != true`, còn **2.555 câu tự gõ**.

Không đưa tệp dữ liệu gốc lên kho công khai. Các mã `turn_id` dưới đây cho phép
trợ giảng có bộ dữ liệu nội bộ kiểm lại.

## Phương pháp đếm có thể lặp lại

1. Lọc `cohort_hint = K4`.
2. Với nhu cầu làm rõ, loại câu mẫu rồi tìm không phân biệt hoa thường trong
   `student_question` bằng biểu thức:
   `không hiểu|chưa hiểu|giải thích|ví dụ|khác nhau|tại sao|là gì|nghĩa là gì|như thế nào`.
3. Đếm cả số lượt và số `student` duy nhất.
4. Để kiểm tra khoảng trống quan sát mức hiểu, đếm số dòng có
   `understanding_level` khác rỗng và số dòng có
   `move_used = ask_probing_question`.
5. Đếm thêm `has_citation = false` và `rating` khác rỗng để mô tả giới hạn của
   tín hiệu hiện có; hai số này không dùng để khẳng định học viên chưa hiểu.

## Kết quả

| Chỉ số | Kết quả | Cách hiểu |
|---|---:|---|
| Câu tự gõ có dấu hiệu cần giải thích/làm rõ | **879 / 2.555 (34,4%)** | Nhu cầu làm rõ xuất hiện thường xuyên trong câu tự gõ |
| Học viên có ít nhất một lượt khớp | **243 / 448 (54,2%)** | Hơn một nửa học viên K4 từng phát tín hiệu cần làm rõ theo quy tắc trên |
| Lượt có `understanding_level` | **6 / 3.097 (0,2%)** | Trường đo mức hiểu gần như trống, không đủ tạo bức tranh lớp |
| Lượt dùng `ask_probing_question` | **6 / 3.097 (0,2%)** | Luồng hiện tại hiếm khi hỏi ngược để kiểm tra hiểu |
| Lượt trả lời không có trích dẫn | **839 / 3.097 (27,1%)** | Cần giữ nguồn cạnh câu hỏi/chẩn đoán để giảng viên kiểm lại |
| Lượt có rating(đánh giá) | **12 / 3.097 (0,4%)** | Rating quá thưa để thay cho kiểm tra mức hiểu có chủ đích |

Phép đếm từ khóa chỉ là proxy(chỉ báo gần đúng): nó đo nhu cầu làm rõ được thể
hiện bằng câu chữ, không khẳng định 879 lượt đều là “không hiểu”. Vì vậy sản phẩm
không chẩn đoán cá nhân; nó tạo một lượt kiểm tra ngắn và chỉ tổng hợp khi đủ phản hồi.

## Ví dụ nguyên văn đã ẩn danh

| Mã lượt | Trích ngắn |
|---|---|
| `T10317` | “giải thích lại dc không hơi khó hiểu” |
| `T10320` | “Bốn làn sóng là gì” |
| `T10326` | “Giải thích lại giúp mình phần mà mình hay thấy khó.” |
| `T10350` | “mask và polygon là gì” |
| `T10399` | “AI khác Machine Learning như thế nào?” |

## Kết luận dùng cho quyết định sản phẩm

Dữ liệu cho thấy nhu cầu làm rõ phổ biến nhưng tín hiệu trực tiếp về mức hiểu của
cả lớp gần như không có. Lát cắt được chọn là: sau một phần bài học, tạo câu hỏi
ngắn có nguồn, thu phản hồi ẩn danh theo lớp và đưa bằng chứng để giảng viên quyết
định tiếp tục, làm rõ hay giảng lại. Đây là công cụ hỗ trợ quyết định, không phải
công cụ chấm điểm hoặc kết luận năng lực từng học viên.
