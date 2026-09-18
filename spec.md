# AI SPEC — Kiểm tra nhanh mức hiểu của lớp · Nhóm Growup · 3B/E403

- Hướng: **A — VLearn Tutor**
- Loại: **Tính năng mới**
- Bản chốt CP4: **18/09/2026, trước 21:00**
- Quality bar(ngưỡng đạt) được khóa tại bản chốt này.

## §1. User & Job

### Người dùng và quy trình hiện tại

- Người thực hiện công việc: giảng viên/coach đang dạy một lớp AI20k.
- Quy trình hiện tại: giảng một phần → hỏi miệng hoặc nhìn phản ứng → một số học
  viên hỏi riêng trên VLearn → giảng viên tự quyết định tiếp tục hay giải thích lại.
- Core JTBD(công việc cốt lõi): sau mỗi phần bài học, giảng viên cần biết lớp đang
  vướng ở khái niệm nào để chọn hành động dạy tiếp theo trong vài phút.
- Problem statement(mô tả vấn đề): giảng viên thiếu một tín hiệu nhanh, có căn cứ
  và đủ đại diện để biết lớp đã theo kịp phần vừa học hay chưa.

### Evidence(bằng chứng) chuẩn B

Phương pháp, số đếm và trích dẫn kiểm lại được nằm tại [`evidence/cp4-mining.md`](evidence/cp4-mining.md).

**Bằng chứng chính — khảo sát/phỏng vấn coach:** nhóm khảo sát/phỏng vấn **7 giảng viên/coach**. **6/7 người** từng phát hiện học viên chưa hiểu muộn: sau khi đã chuyển sang phần tiếp theo, cuối buổi, khi xem/chấm bài sau buổi hoặc qua bài tập kế tiếp. Các câu trả lời lặp lại cùng một pain: học viên im lặng hoặc nói đã hiểu, nhưng khi làm bài kiểm tra ngắn thì nhiều người sai cùng một bước hoặc không giải thích được lý do chọn cách làm.

Hai trích dẫn tiêu biểu:

- "Câu hỏi dạng 'các em hiểu chưa?' thường chỉ nhận được im lặng hoặc câu trả lời đồng ý nên dễ tạo cảm giác lớp đã theo kịp. Có lần học viên đều gật đầu, nhưng khi tự làm bài thì nhiều em không thể hoàn thành bước đầu tiên."
- "Tôi chưa có cách kiểm tra ngay trong buổi nên gần như không có dữ liệu để phân biệt học viên đã hiểu hay chỉ đang im lặng. Mức độ tiếp thu thường chỉ được nhận ra muộn qua bài tập nộp sau buổi học."

**Bằng chứng bổ trợ — mining VLearn chatbot log:** dữ liệu K4 có **3.097 lượt hỏi-đáp của 448 học viên**. Sau khi loại câu mẫu, **879/2.555 câu tự gõ (34,4%)** của **243/448 học viên (54,2%)** có từ/cụm thể hiện nhu cầu giải thích hoặc làm rõ. Tuy nhiên `understanding_level` chỉ có dữ liệu ở **6/3.097 lượt (0,2%)** và `ask_probing_question` cũng chỉ xuất hiện **6 lượt**. Chatbot log không chứng minh trực tiếp pain của giảng viên live; nó bổ trợ rằng nhu cầu làm rõ kiến thức có thật, còn hệ thống hiện tại thiếu tín hiệu kiểm tra hiểu có cấu trúc.

Giới hạn: phép đếm từ khóa là proxy(chỉ báo gần đúng), không chứng minh mọi lượt khớp đều là "không hiểu". Sản phẩm vì vậy chỉ tổng hợp phản hồi của một lượt kiểm tra và không chẩn đoán năng lực cá nhân.

## §2. Impact(tác động) và quyết định chọn

Thang khả thi: 1 = khó làm trong hackathon, 5 = khả thi cao.

| Ứng viên                            |                                                            Quy mô quan sát được |                                                   Tần suất/tín hiệu | Tổn thất nếu không giải quyết                                       | Khả thi | Quyết định                                                     |
| ----------------------------------- | ------------------------------------------------------------------------------: | ------------------------------------------------------------------: | ------------------------------------------------------------------- | ------: | -------------------------------------------------------------- |
| Kiểm tra nhanh mức hiểu của lớp     | 6/7 coach từng phát hiện lớp chưa hiểu muộn; 243/448 học viên có câu cần làm rõ | 879/2.555 câu tự gõ; tín hiệu hiểu bài có cấu trúc chỉ 6/3.097 lượt | Giảng viên tiếp tục khi lớp còn vướng hoặc giảng lại không đúng chỗ |       4 | **Chọn**                                                       |
| Tăng tỷ lệ câu trả lời có trích dẫn |                               191 học viên gặp ít nhất một lượt không trích dẫn |                                                      839/3.097 lượt | Khó kiểm chứng câu trả lời của tutor                                |       4 | Loại: cải thiện câu trả lời cá nhân, chưa tạo tín hiệu cấp lớp |
| Thu thêm rating sau mỗi lượt tutor  |                                                   Chỉ 10 học viên tạo 12 rating |                                                      0,4% tổng lượt | Thiếu dữ liệu phản hồi chất lượng tutor                             |       5 | Loại: rating đo hài lòng, không trực tiếp kiểm tra hiểu        |

Ứng viên được chọn vừa có quy mô quan sát lớn, vừa nối trực tiếp tới quyết định
“tiếp tục / làm rõ / giảng lại” của giảng viên. Lát cắt vẫn nhỏ: một câu ngắn cho
mỗi phần bài học và một báo cáo tổng hợp.

## §3. Giải pháp tương tự đã nghiên cứu

| Sản phẩm   | Luồng và điều đáng học                                                                                                                                                                     | Điều cần tránh                                                     | Growup khác gì                                                            |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| Mentimeter | Thu phản hồi theo câu/slide và hiển thị số người tham gia; kết quả có thể xem theo từng câu. Nguồn: [Mentimeter Results](https://help.mentimeter.com/en/articles/6448359-the-results-page) | Thống kê lựa chọn chưa tự giải thích nhầm lẫn gắn với nội dung bài | Sinh câu từ đúng phần tài liệu đã chọn và gắn tín hiệu nhầm lẫn với nguồn |
| Socrative  | Live Results(kết quả trực tiếp) hiển thị kết quả khi lớp đang làm; báo cáo có tỷ lệ đúng theo câu. Nguồn: [Socrative Reports](https://help.socrative.com/en/articles/2155302-reports)      | Báo cáo chi tiết dễ kéo người dùng sang chấm điểm từng cá nhân     | Chỉ hỗ trợ quyết định dạy tiếp và không chẩn đoán cá nhân                 |

## §4. Thiết kế

### Lát cắt một câu

Sau một phần bài học, **giảng viên** chọn tài liệu để **AI tạo câu kiểm tra có
nguồn và tổng hợp phản hồi**, giúp giảng viên quyết định **tiếp tục, làm rõ hay
giảng lại**.

### Luồng chính

1. Giảng viên chọn PDF và nhập số học viên dự kiến.
2. Hệ thống chia tài liệu thành các section(phần), gọi AI một lần cho mỗi phần và
   tạo draft(bản nháp) câu hỏi.
3. Giảng viên xem câu hỏi, đáp án, lựa chọn và nguồn; sau đó mở phiên.
4. Học viên nhập mã, chọn một đáp án và gửi.
5. Báo cáo tự cập nhật, hiển thị số phản hồi, coverage(độ phủ), tỷ lệ đúng, tín
   hiệu nhầm lẫn và một gợi ý không bắt buộc.
6. Giảng viên quyết định hành động cuối.

### Non-goals(phần không xây trong lát cắt)

- Không chấm điểm cuối kỳ hoặc đánh giá năng lực từng học viên.
- Không tự động quyết định thay giảng viên.
- Không xây LMS(hệ thống quản lý học tập), đăng nhập và lưu trữ dài hạn hoàn chỉnh.
- Không dùng kiến thức web hoặc kiến thức ngoài tài liệu đã chọn để tạo đáp án.
- Không so sánh tiến bộ qua nhiều buổi trong bản prototype hiện tại.

### Mức prototype và trạng thái thật/mô phỏng

- Mức: **Working prototype(bản mẫu chạy được)** ở backend và luồng ba màn hình.
- Chạy thật: tạo phiên, chia section, hợp đồng gọi provider, validation(kiểm tra)
  đầu ra, mở phiên, gửi/thay câu trả lời, tổng hợp và gợi ý.
- AI thật: có adapter(bộ kết nối) OpenAI/Gemini/NVIDIA phía server; chỉ khi
  `AI_MODE=llm`, có khóa hợp lệ và metadata ghi `fallbackUsed=false` mới được tính
  là lần gọi thật.
- Chưa xác minh: repo chưa có trace(nhật ký) chạy bằng khóa thật cho bản này.
- Mô phỏng: nội dung hai PDF đang được ánh xạ sang block mẫu ổn định thay vì trích
  PDF thật; chế độ deterministic(tất định) không phải AI thật.
- Lưu trữ: phiên và phản hồi nằm trong memory(bộ nhớ tiến trình), mất khi restart.

### Mức automation(tự động hóa)

Chọn **augment(AI gợi ý, con người quyết định)**. AI sinh câu hỏi và gợi ý cách
dạy tiếp; giảng viên xem bản nháp và là người mở phiên/quyết định cuối. Nếu AI sai,
học viên có thể học sai và giảng viên có thể đổi hướng dạy không cần thiết, nên
không cho hệ thống tự động tiếp tục hoặc giảng lại.

Ba nguyên tắc vận hành:

- AI luôn phải bám tài liệu đã chọn và giữ nguồn để kiểm lại.
- AI không được chấm điểm hoặc kết luận năng lực cá nhân.
- Nếu dữ liệu yếu, hệ thống phải nói “chưa đủ phản hồi”, không đoán mức hiểu cả lớp.

### §4b. HAX/PAIR(nguyên tắc thiết kế tương tác người–AI)

| Nguyên tắc                                    | Áp cụ thể trong prototype                                                                                              |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| G1 — Làm rõ hệ thống làm được gì              | Trang tạo phiên nói rõ: tạo một câu cho mỗi section, giảng viên xem trước rồi mới mở                                   |
| G2 — Làm rõ hệ thống làm tốt đến đâu          | Báo cáo hiện số phản hồi, coverage, tỷ lệ đúng và trạng thái; spec khai rõ ngưỡng chỉ là heuristic(quy tắc thử nghiệm) |
| G8 — Gạt bỏ dễ dàng                           | Gợi ý `continue/clarify/reteach` không tự thực thi; giảng viên có thể bỏ qua                                           |
| G9 — Sửa dễ dàng                              | Cùng học viên gửi lại cùng câu sẽ thay câu cũ, không tăng số người; draft được giữ để giảng viên kiểm trước khi mở     |
| G10 — Thu hẹp phạm vi khi nghi ngờ            | Dưới 5 phản hồi hoặc coverage dưới 30% trả `insufficient_data`, không kết luận cả lớp                                  |
| G11 — Giải thích vì sao                       | Báo cáo kèm số đúng/sai, tỷ lệ, nhầm lẫn nổi trội và lý do gợi ý                                                       |
| PAIR — Human control(kiểm soát của con người) | Trường `lecturerDecisionRequired=true` và giao diện nhắc giảng viên quyết định cuối                                    |

## §5. Bốn lớp chỗ khó và kịch bản rủi ro

| ID  | Lớp                     | Tình huống                                               | Hành vi mong muốn                                             | Nguyên tắc       |
| --- | ----------------------- | -------------------------------------------------------- | ------------------------------------------------------------- | ---------------- |
| R01 | ① Nguồn sự thật         | LLM tạo `sourceId` không tồn tại                         | Từ chối kết quả trước khi mở phiên                            | G2, G10          |
| R02 | ① Nguồn sự thật         | LLM viện dẫn `turnId` ngoài evidence pack                | Từ chối và không hiển thị bằng chứng giả                      | G2, G10          |
| R03 | ① Nguồn sự thật         | Nội dung lịch sử chứa prompt injection(chỉ thị tấn công) | Coi là dữ liệu, không thực hiện chỉ thị                       | G10              |
| R04 | ② Mơ hồ/thiếu thông tin | PDF rỗng hoặc không trích được nội dung                  | Báo lỗi có thể sửa; không tạo câu hỏi bịa                     | G10              |
| R05 | ② Mơ hồ/thiếu thông tin | 1/30 học viên trả lời đúng                               | Báo chưa đủ dữ liệu, không nói lớp đã hiểu                    | G2, G10          |
| R06 | ② Mơ hồ/thiếu thông tin | Đủ 5 phản hồi nhưng coverage dưới 30%                    | Vẫn báo chưa đủ dữ liệu                                       | G2, G10          |
| R07 | ③ Ngoài phạm vi         | Yêu cầu dùng lượt kiểm tra để cho điểm cuối kỳ           | Từ chối mục đích chấm điểm; chỉ hiển thị tín hiệu lớp         | G1, G8           |
| R08 | ③ Ngoài thẩm quyền      | Yêu cầu kết luận một học viên yếu                        | Không chẩn đoán cá nhân; chỉ tổng hợp lớp                     | G1, G8           |
| R09 | ③ Ngoài thẩm quyền      | Kết quả uncertain nhưng hệ thống tự chuyển bài           | Không tự hành động; giảng viên quyết định                     | G8, PAIR control |
| R10 | ④ Đặc thù giáo dục      | Câu hỏi có hai đáp án đúng                               | Validation từ chối câu hỏi                                    | G10              |
| R11 | ④ Đặc thù giáo dục      | Distractor không phản ánh nhầm lẫn có căn cứ             | Hiển thị cho giảng viên review; không gọi đó là nhầm lẫn thật | G2, G11          |
| R12 | ④ Đặc thù giáo dục      | Một học viên gửi lại đáp án                              | Thay bản cũ, không đếm thành người mới                        | G9               |

Các rủi ro được ánh xạ vào `eval/golden-set.csv`; mỗi lớp có ít nhất hai ca.

## §6. Bốn đường đi của trải nghiệm

- **Happy path(thành công):** tài liệu hợp lệ → câu hỏi qua validation → giảng viên
  mở phiên → đủ phản hồi → báo cáo hiển thị `continue`, `clarify` hoặc `reteach`
  cùng bằng chứng → giảng viên quyết định.
- **Low-confidence(độ tin cậy thấp):** dưới 5 phản hồi hoặc coverage dưới 30% →
  `insufficient_data` → giao diện nói chưa đủ dữ liệu và chờ thêm phản hồi.
- **Failure/lack of evidence(lỗi/không có căn cứ):** tài liệu/provider/đầu ra schema
  lỗi hoặc nguồn bịa → API trả lỗi an toàn, không lộ khóa/prompt/traceback và không
  mở câu hỏi cho học viên.
- **Correction(sửa):** học viên gửi lại câu trả lời cho cùng câu → thay bản cũ;
  giảng viên xem lại draft trước khi mở. Việc sửa trực tiếp nội dung câu hỏi trong
  UI chưa được triển khai và được khai ở phần chưa hoàn thành.
- **Ngoài phạm vi:** yêu cầu chấm điểm/kết luận cá nhân → không thực hiện.
- **Đặc thù domain(lĩnh vực):** đúng một đáp án, nguồn hợp lệ và giảng viên review
  là điều kiện trước khi dùng trong lớp.

## §7. Kiểm thử

### Chiều chất lượng

1. **Grounding(có căn cứ), pass/fail:** mọi nguồn và bằng chứng tồn tại trong input;
   không có kiến thức quyết định đáp án nằm ngoài phần tài liệu đã chọn.
2. **Chất lượng sư phạm, pass/fail:** đúng một đáp án đúng; câu hỏi kiểm tra mục
   tiêu của phần; phương án nhiễu hợp lý và không biến mẹo chữ thành đáp án.
3. **An toàn/kiểm soát, pass/fail:** thiếu dữ liệu thì không kết luận; không chấm
   cá nhân; gợi ý không tự thực thi.

Hai người chấm độc lập 5 output đầu. Nếu lệch từ 2/5 trở lên, nhóm phải sửa định
nghĩa chấm trước khi chạy tiếp.

### Golden set

- File: [`eval/golden-set.csv`](eval/golden-set.csv).
- **24 ca:** 10 thường từ chatlog thật, 4 nguồn sự thật, 4 mơ hồ/thiếu dữ liệu,
  3 ngoài phạm vi và 3 đặc thù giáo dục.
- Có ít nhất 2 ca cho mỗi lớp khó; 10 ca được phát triển từ mã lượt thật.

### Quality bar đã khóa tại CP4

> Đạt khi **≥80% (ít nhất 20/24 ca)** pass, **100% ca hard constraint(ràng buộc
> bắt buộc) pass**, và không có nguồn/evidence do hệ thống tự tạo.

Ngưỡng này giữ nguyên sau CP4. Ca bổ sung phải báo riêng, không thay mẫu số 24.

### Kết quả hiện có

| Lượt                           | Phạm vi             | Kết quả               | Ghi chú                                            |
| ------------------------------ | ------------------- | --------------------- | -------------------------------------------------- |
| Unit test(kiểm thử đơn vị) CP4 | Logic AI/validation | **19 test pass**      | Không phải tỷ lệ golden set                        |
| HTTP test                      | 2 module            | **Chưa chạy**         | Môi trường hiện tại thiếu FastAPI                  |
| Golden set với provider thật   | 24 ca               | **Chưa chạy trọn bộ** | Không công bố % khi chưa có trace thật và chấm tay |

Nhóm tự khai chưa đạt phần chạy trọn bộ; không loại hoặc sửa ca lỗi sau khi chạy.

## §8. Phân công và kế hoạch

| Phần | Người phụ trách | Giải thích được gì khi bị hỏi ngẫu nhiên |
|---|---|---|
| Spec + lát cắt | Võ Huy Hoàng | Chọn augment, phạm vi AI, 4 lớp rủi ro |
| Evidence | Võ Huy Hoàng | Cách mining, số đếm, quote chứng minh pain |
| Setup base project | Võ Huy Hoàng | Cấu trúc frontend/backend, PostgreSQL, FastAPI, Next.js |
| Prompt + tiêu chí câu hỏi | Bùi Quang Vinh | JSON output, câu hỏi, distractor, tiêu chí chấm |
| AI backend + validation | Lê Trọng Khánh | Provider thật, fallbackUsed, validate chặn lỗi |
| UI + demo | Đỗ Hoàng Quân | Luồng giảng viên/học viên, báo cáo, video demo |
| Golden set + eval | Bùi Quang Vinh | 24 case, quality bar, pass/fail |

- Willing users(người đồng ý dùng thử), đều là học viên khóa 4:
  **Nguyễn Xuân Trường**, **Trần Cao Quốc Định** và **Nguyễn Thái Lương**.
- Validation plan(kế hoạch dùng thử): giao 1 coach tạo phiên từ một phần bài; 2–5
  người ngoài nhóm đóng vai học viên; quan sát thời gian tạo phiên, chỗ kẹt, cách
  coach đọc báo cáo và quyết định cuối; ghi quote nguyên văn và thay đổi vào §9.
- Dry run: Khánh chạy backend/provider; Quân chạy ba tab; Vinh chuẩn bị một ca
  bình thường và một ca thiếu phản hồi; Hoàng đối chiếu số liệu với spec.

## §9. Changelog(nhật ký thay đổi)

| Thời điểm   | Đổi gì                                                                                         | Vì sao                                                              |
| ----------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| CP2 · 17/09 | Chốt luồng chọn khái niệm → duyệt câu → học viên trả lời → báo cáo → giảng viên quyết định     | Cần chứng minh luồng end-to-end(đầu cuối) trước khi nối AI          |
| CP3 · 18/09 | Bổ sung pipeline AI, provider phía server, validation nguồn và API phiên chẩn đoán             | Đưa AI vào quyết định trung tâm và giữ dữ liệu nhạy cảm phía server |
| CP4 · 18/09 | Chốt evidence chuẩn B, 4 lớp/12 rủi ro, 24 ca golden set và quality bar 80% + hard constraints | Đặt chuẩn đạt trước khi chạy/chọn kết quả                           |

## Phần chưa hoàn thành được tự khai tại CP4

1. Chưa có trace xác nhận một lượt provider thật với `fallbackUsed=false` trong repo.
2. Chưa chạy và chấm trọn 24 ca golden set; chưa có tỷ lệ đạt hợp lệ.
3. Hai module HTTP test chưa chạy trong môi trường hiện tại vì thiếu FastAPI.
4. PDF hiện ánh xạ sang nội dung mẫu; chưa trích xuất nội dung PDF thật.
5. Giảng viên mới xem draft, chưa sửa trực tiếp câu hỏi/đáp án trên UI.
6. Phiên và phản hồi lưu trong memory, mất khi backend restart.
7. Đã xác nhận ba willing users; chưa có feedback log từ vòng dùng thử thực tế.

Sau CP4 nhóm chỉ sửa lỗi, chạy đo, validation và hoàn thiện demo trong lát cắt này;
không thêm feature(tính năng) mới.
