# Danh sách việc cần làm — Nhóm Growup · 3B · E403

Tổng hợp từ README.md, 01-challenge-brief.md, 02-guide.md, 03-ai-spec-template.md và 04-rubric.md.

Hiện trạng kiểm tra ngày 17/09/2026: thư mục đang chứa tài liệu đề bài và dữ liệu mẫu; bảng thành viên còn trống, chưa thấy canvas.md, spec.md, codebase/, eval/, validation/, reflection/ hoặc slide của nhóm. Các ô dưới đây chưa đánh dấu vì chưa có bằng chứng hoàn thành trong thư mục; không có nghĩa nhóm chưa làm bên ngoài.

## 1. CP1 — 19:30 ngày 17/09: chốt bài toán và nhóm

- [ ] Chọn đội trưởng; điền họ tên, mã học viên, phòng E403, cụm thi, thành viên và phân công vào README.md.
- [ ] Chọn track(hướng đề tài) A–E và đề cụ thể, phục vụ người trong chương trình AI20k.
- [ ] Viết vấn đề: ai — đang làm gì — vướng đâu — hậu quả gì; câu mô tả vấn đề không có chữ AI.
- [ ] Viết lát cắt một câu: một người dùng · một công việc · một quyết định AI · một kết quả.
- [ ] Lưu canvas(bản tóm tắt dự án) 7 dòng vào canvas.md: hướng đề tài, người thực hiện công việc, vấn đề, bằng chứng đầu, lát cắt, mức tự động hóa + người đồng ý thử, phân công có tên.
- [ ] Có 1–2 bằng chứng đầu, ghi số liệu và cách kiểm lại.
- [ ] Mời ít nhất 2 người ngoài nhóm đồng ý dùng thử từ CP1; nên chuẩn bị 3 người theo hướng dẫn Canvas.
- [ ] Chuẩn bị kho mã GitHub công khai đúng tên K4-3B-E403-Growup; kiểm tra mở được bằng cửa sổ ẩn danh.
- [ ] Kiểm tra kho nộp bài được tạo mới, không mang nguyên dữ liệu đề bài lên kho công khai.
- [ ] Lấy đường dẫn biểu mẫu từ Discord/VLearn; nộp Canvas, thông tin đội trưởng và đường dẫn kho mã đúng hạn.

## 2. CP2 — 21:00 ngày 17/09: thể hiện luồng hoạt động

- [ ] Vẽ luồng từ đầu vào đến kết quả; thể hiện người dùng thao tác gì ở mỗi bước.
- [ ] Làm prototype(bản mẫu) bấm qua được luồng chính; hoặc chuẩn bị sơ đồ/video theo lựa chọn README cho phép.
- [ ] Ghi rõ phần mô phỏng và phần chạy thật; CP2 chưa cần AI chạy thật.
- [ ] Lưu phiên bản đầu vào kho mã để đáp ứng mục xác minh trong rubric(bảng tiêu chí chấm điểm).
- [ ] Nộp sản phẩm thể hiện luồng đúng hạn; gọi trợ giảng nếu đang kẹt kỹ thuật.

## 3. CP3 — 16:00 ngày 18/09: AI thật và phép đo đầu tiên

- [ ] Xây luồng chạy từ đầu đến cuối theo đúng lát cắt, không sửa kết quả bằng tay giữa chừng.
- [ ] Có ít nhất 1 lời gọi AI thật tại quyết định trung tâm; lưu nhật ký đã loại thông tin nhạy cảm.
- [ ] Xây golden set(bộ ca kiểm thử chuẩn) ít nhất 20 ca trong eval/.
- [ ] Phủ ít nhất 2 ca cho mỗi lớp khó, 8–10 ca thường và 2–4 ca hiếm; chọn cơ cấu cộng lại đủ ít nhất 20 ca.
- [ ] Có ít nhất 10 ca lấy hoặc phát triển từ dữ liệu thật phù hợp hướng đề tài; ghi mã nguồn tham chiếu.
- [ ] Định nghĩa 2–3 chiều chất lượng bằng tiêu chí kiểm chứng được, kèm kết quả mong muốn cho từng ca.
- [ ] Đặt quality bar(ngưỡng đạt chất lượng) bằng số trước lượt đo dùng để đánh giá; chốt chính thức tại CP4.
- [ ] Chạy trọn bộ ít nhất 1 lượt; ghi mọi ca đạt/chưa đạt, tỷ lệ đạt và nguyên nhân lỗi.
- [ ] Quay video 30 giây thao tác thật, thấy AI trả kết quả thật.
- [ ] Nộp video và số đo đúng hạn; không che giấu kết quả chưa đạt.

## 4. CP4 — 21:00 ngày 18/09: chốt spec.md

- [ ] Tạo spec(bản đặc tả) từ 03-ai-spec-template.md; sửa phần chọn hướng thành A–E cho khớp đề bài hiện hành.
- [ ] §1: mô tả người dùng, công việc, quy trình hiện tại và vấn đề có bằng chứng.
- [ ] Bằng chứng đạt chuẩn A và/hoặc B: A = khảo sát ít nhất 20 người ngoài nhóm, ít nhất 50% xác nhận và có đầy đủ nhật ký; B = số đếm + ít nhất 5 ví dụ nguyên văn có nguồn + phương pháp đếm kiểm lại được.
- [ ] Nếu chọn C, kiểm tra yêu cầu riêng: tracks/README.md nêu phỏng vấn ít nhất 3 người và/hoặc khai thác bản chép lời/slide; ghi rõ cơ sở áp dụng vì rubric chung dùng chuẩn A/B.
- [ ] §2: so sánh ít nhất 3 bài toán bằng số người gặp, tần suất, tổn thất mỗi lần và khả thi; giữ lý do loại các phương án khác.
- [ ] §3: nghiên cứu giải pháp tương tự; ghi luồng, điều đáng học, điều cần tránh và điểm khác biệt.
- [ ] §4: lát cắt khớp bản mẫu, ít nhất 3 việc ngoài phạm vi, mức bản mẫu và phần mô phỏng/thật.
- [ ] Chọn mức AI hỗ trợ người quyết / tự làm có điều kiện / tự động hoàn toàn; giải thích bằng hậu quả nếu AI sai.
- [ ] Áp dụng ít nhất 4 nguyên tắc HAX/PAIR(hướng dẫn thiết kế tương tác người–AI), trỏ vào vị trí cụ thể; có G10 thu hẹp phạm vi khi không chắc, ít nhất 1 nguyên tắc khởi đầu và ít nhất 1 trong G8/G9/G11 theo guide.
- [ ] §5: cụ thể hóa 4 lớp khó: nguồn sự thật; mơ hồ/thiếu thông tin; ngoài phạm vi/thẩm quyền; đặc thù lĩnh vực.
- [ ] Có ít nhất 8 kịch bản rủi ro, ghi tình huống và hành vi mong muốn, phủ đủ 4 lớp.
- [ ] §6: thể hiện 4 đường trải nghiệm trong đặc tả và bản mẫu: thành công; không chắc; lỗi/không có căn cứ; người dùng sửa.
- [ ] §7: tiêu chí đo, bộ ca thử, ngưỡng đạt bằng số và bảng kết quả.
- [ ] §8: phân công có tên và kế hoạch dùng thử; §9: nhật ký thay đổi có lý do.
- [ ] Lưu phiên bản spec.md trước hạn; giữ nguyên chuẩn đạt sau CP4, khai rõ phần chưa hoàn thành.
- [ ] Nộp đường dẫn spec.md và tiến độ đúng hạn; sau CP4 tập trung sửa lỗi, không thêm tính năng mới theo guide.

## 5. CP5 — 22:30 ngày 18/09: dùng thử và nộp cuối

- [ ] Nếu lấy 8 điểm R6: tổ chức dùng thử với 5 người ngoài nhóm, trong đó 2 người đã khai CP1, theo yêu cầu README.
- [ ] Lưu validation(nhật ký kiểm chứng với người dùng): ai/vai trò, nhiệm vụ, quan sát/chỗ kẹt, lời nói nguyên văn, quyết định.
- [ ] Ghi ít nhất 1 thay đổi từ phản hồi vào §9; nếu giữ nguyên phải có lý do căn cứ.
- [ ] Cuối nhật ký ghi: chủ đề lặp nhiều nhất; sửa gì trước trình bày; giữ gì và vì sao; việc để sau.
- [ ] Chuẩn bị 6 slide(trang trình chiếu): người dùng và vấn đề; lý do chọn; giải pháp và thao tác; kết quả đo; phản hồi thật hoặc phân tích kết quả thử; ưu tiên nếu có thêm 1 tuần.
- [ ] Mỗi trang có ít nhất 1 số liệu, lời trích có nguồn hoặc kết quả đo kiểm chứng được.
- [ ] Xuất demo-slides.pdf; quay video trình diễn dự phòng đúng phần định trình bày. Video này khác video 30 giây CP3.
- [ ] Chuẩn bị 1 ca bình thường và 1 ca khó/lỗi; trình bày tỷ lệ đạt so với ngưỡng đã chốt.
- [ ] Tập trình bày có bấm giờ: E403 vòng cụm 6 phút; nếu vào chung kết, 7 phút trình bày + 3 phút hỏi đáp theo README.
- [ ] Hoàn thiện kho bài nộp: README.md, canvas.md, spec.md, demo-slides.pdf, codebase/, eval/, validation/ nếu làm R6, reflection/.
- [ ] Mỗi thành viên có reflection(bài tự đánh giá) riêng: vai trò, phần đã làm, AI hỗ trợ thế nào, bài học từ một ca lỗi của nhóm.
- [ ] Kiểm tra quyền xem kho mã, PDF, video và đường dẫn nộp; nộp hết trước CP5 vì README quy định không nộp thêm sau mốc này.

## 6. CP6 — 09:00 ngày 19/09: thuyết trình

- [ ] Có sẵn PDF và video dự phòng, kiểm tra chạy được.
- [ ] Mỗi thành viên hiểu và giải thích được phần được phân công.
- [ ] Chuẩn bị trả lời: vì sao chọn mức tự động hóa; lỗi nguy hiểm nhất; kết quả chưa đạt vì sao; người dùng đã khiến nhóm thay đổi gì.
- [ ] Sẵn sàng chạy một ca mới nếu giám khảo yêu cầu; không nộp thêm tài liệu ở CP6.

## 7. Kiểm tra dữ liệu trước khi công khai

- [ ] Không đưa nguyên data/ của đề bài vào kho nộp công khai; chỉ trích ngắn và dẫn mã theo quy định.
- [ ] Không chia sẻ dữ liệu ra ngoài khóa, không suy đoán danh tính người đã ẩn danh; đưa vào công cụ AI ngoài ở mức tối thiểu.
- [ ] Với ví dụ Discord, trích tối đa 2 câu; báo ban tổ chức nếu phát hiện sót thông tin cá nhân.
- [ ] Không đưa khóa truy cập, mật khẩu hoặc thông tin cá nhân vào mã nguồn, nhật ký và video.

## Điểm ưu tiên và các hướng dẫn chưa thống nhất

- Nộp đúng hạn CP1–CP5: 25 điểm, mỗi mốc 5 điểm; muộn mất điểm mốc đó.
- Bằng chứng R1 + thiết kế R2 + kiểm thử R4: tổng 45 điểm, nên ưu tiên trước việc làm đẹp giao diện.
- R6: tối đa 8 điểm; không làm thì tổng tối đa 92 điểm.
- Người nộp: README yêu cầu đội trưởng nộp cả 5 mốc bằng cùng mã học viên; 04-rubric.md lại ghi mỗi thành viên nộp riêng. Tạm lập kế hoạch theo README dành cho ca 3B, đối chiếu thông báo khai mạc hoặc hỏi trợ giảng trước khi nộp.
- Người dùng thử: README yêu cầu 5 người, rubric yêu cầu ít nhất 2; Canvas trong guide/ví dụ đề nghị 3 người từ CP1. Chuẩn bị 3 người từ CP1 và thử 5 người trước CP5 đáp ứng cả các mức này.
- CP2: README cho phép sơ đồ luồng, rubric muốn bản mẫu bấm được và có phiên bản lưu trong kho. Làm bản mẫu bấm được sẽ đáp ứng cả hai.
- Thời lượng trình bày: guide/rubric ghi 5 phút + 5 phút hỏi đáp, README ghi thể thức E403 như trên. Đối chiếu thể lệ khai mạc; chưa đủ căn cứ xác định tài liệu nào là bản cuối.
- Mẫu spec còn danh sách 3 hướng cũ; dùng A–E từ đề bài và tracks/README.md.

Nguồn tra cứu: README.md (lịch, cách nộp, cấu trúc, bảo mật); 01-challenge-brief.md (nghiệm thu); 02-guide.md (cách làm, slide); 03-ai-spec-template.md (đặc tả); 04-rubric.md (tiêu chí điểm); tracks/README.md và đề riêng (yêu cầu theo hướng).
