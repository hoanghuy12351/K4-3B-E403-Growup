import Link from "next/link";
import { Button, Tag } from "antd";
import PublicHeader from "@/components/PublicHeader";

const steps = [
  { icon: "📤", title: "Tải bài giảng", text: "Đưa file PPTX lên. Hệ thống đọc nội dung, ghi chú và hình ảnh trong bài giảng." },
  { icon: "🧠", title: "AI chia phần lớn", text: "AI nhận diện mạch kiến thức, chọn ba ý trọng tâm và đề xuất checkpoint phù hợp." },
  { icon: "✨", title: "Duyệt câu hỏi", text: "AI soạn ba câu hỏi ngắn. Giảng viên chỉnh sửa và duyệt trước khi sử dụng." },
  { icon: "🚀", title: "Dạy và kiểm tra", text: "Học viên nhập mã phòng, trả lời và giảng viên thấy ngay lớp đang vướng ở đâu." },
];

const benefits = [
  ["📚", "Không chia vụn bài học", "Mỗi checkpoint nằm sau một phần kiến thức lớn, không phải sau từng slide."],
  ["🎯", "Ba ý quan trọng nhất", "Mỗi câu kiểm tra một mục tiêu rõ ràng để dễ nhận ra chỗ lớp chưa hiểu."],
  ["🙋", "Giảng viên giữ quyền mở", "Câu hỏi chỉ xuất hiện khi giảng viên sẵn sàng mở cho cả lớp."],
  ["🛡️", "Không đoán khi thiếu dữ liệu", "Hệ thống báo chưa đủ dữ liệu nếu số người phản hồi còn thấp."],
];

export default function HomePage() {
  return <div className="landing-page playful-theme">
    <PublicHeader />
    <main>
      <section className="hero-section">
        <div className="hero-copy">
          <div className="hero-pill"><span>✨</span> AI đồng hành cùng lớp học</div>
          <h1>Biết lớp đã hiểu<br /><span>trước khi dạy tiếp.</span></h1>
          <p>Tải slide lên, để AI đề xuất checkpoint và ba câu hỏi ngắn. Bạn vẫn là người duyệt, mở câu hỏi và quyết định nhịp dạy.</p>
          <div className="hero-actions">
            <Link href="/register"><Button type="primary" size="large">Bắt đầu miễn phí</Button></Link>
            <Link href="/join"><Button size="large">Nhập mã phòng</Button></Link>
          </div>
          <div className="hero-trust"><span>✓ Không cần cài đặt</span><span>✓ Học viên không cần tài khoản</span></div>
        </div>
        <div className="lesson-demo" aria-label="Minh họa tạo checkpoint từ slide">
          <div className="demo-window-bar"><i /><i /><i /><span>Bài giảng: Nhập môn AI</span></div>
          <div className="demo-body">
            <div className="slide-stack">
              <div className="mini-slide"><b>01</b><span>Khái niệm nền tảng</span></div>
              <div className="mini-slide active"><b>02</b><span>Mô hình học thế nào?</span></div>
              <div className="mini-slide"><b>03</b><span>Ví dụ thực tế</span></div>
            </div>
            <div className="ai-suggestion">
              <span className="ai-orb">✨</span><Tag color="green">AI đã phân tích</Tag>
              <h2>Checkpoint sau slide 12</h2>
              <p>Ba khái niệm trọng tâm đã sẵn sàng để kiểm tra.</p>
              <div className="concept-chip">🎯 Mô hình học từ dữ liệu</div>
              <div className="concept-chip">🎯 Training và inference</div>
              <div className="concept-chip">🎯 Giới hạn của mô hình</div>
              <Button type="primary" block>Duyệt 3 câu hỏi</Button>
            </div>
          </div>
          <div className="floating-badge badge-one">💡 AI đề xuất</div>
          <div className="floating-badge badge-two">🙌 28 học viên đã vào</div>
        </div>
      </section>
      <section className="value-strip">
        <div><strong>1 file PPTX</strong><span>là điểm bắt đầu</span></div>
        <div><strong>3 câu ngắn</strong><span>cho mỗi phần lớn</span></div>
        <div><strong>Không tài khoản</strong><span>cho học viên</span></div>
        <div><strong>Giảng viên quyết định</strong><span>AI chỉ đề xuất</span></div>
      </section>
      <section className="landing-section" id="cach-hoat-dong">
        <div className="section-heading"><p className="eyebrow">CÁCH HOẠT ĐỘNG</p><h2>Bốn bước để nghe được<br />“nhịp hiểu” của lớp</h2><p>Ít thao tác hơn, nhiều tín hiệu hữu ích hơn trong lúc dạy.</p></div>
        <div className="flow-grid">{steps.map((step, index) =>
          <article className="flow-card" key={step.title}>
            <span className="step-bubble">{step.icon}</span><span className="step-number">0{index + 1}</span>
            <h3>{step.title}</h3><p>{step.text}</p>
          </article>)}</div>
      </section>
      <section className="classroom-section">
        <div className="classroom-visual">
          <div className="room-code"><small>MÃ PHÒNG</small><strong>OWL42</strong><span>24/30 đã tham gia</span></div>
          <div className="answer-cloud"><span>🤔</span><span>💡</span><span>🙋</span><span>🎯</span><span>😄</span></div>
        </div>
        <div className="classroom-copy"><p className="eyebrow">DÀNH CHO CẢ LỚP</p><h2>Vào lớp trong vài giây</h2><p>Học viên chỉ nhập mã phòng và tên hiển thị. Khi giảng viên mở checkpoint, ba câu hỏi xuất hiện ngay trên thiết bị.</p>
          <ul><li><span>✓</span> Không cần email hay mật khẩu</li><li><span>✓</span> Theo đúng nhịp slide của giảng viên</li><li><span>✓</span> Có thể báo “Tôi chưa hiểu”</li></ul>
          <Link href="/join"><Button type="primary" size="large">Thử vào lớp</Button></Link>
        </div>
      </section>
      <section className="landing-section" id="an-toan">
        <div className="section-heading centered"><p className="eyebrow">THIẾT KẾ CÓ TRÁCH NHIỆM</p><h2>Thông minh, nhưng không tự quyết</h2><p>Growup giúp giảng viên nhìn rõ tín hiệu và luôn nói rõ giới hạn của dữ liệu.</p></div>
        <div className="benefit-grid">{benefits.map(([icon, title, text]) => <article className="benefit-card" key={title}>
          <span>{icon}</span><h3>{title}</h3><p>{text}</p></article>)}</div>
      </section>
      <section className="cta-section"><div><span className="cta-mascot">🌱</span><p className="eyebrow">SẴN SÀNG CHƯA?</p><h2>Biến slide thành một lớp học biết phản hồi.</h2></div>
        <div><Link href="/register"><Button type="primary" size="large">Tạo tài khoản giảng viên</Button></Link><Link href="/login"><Button size="large">Đăng nhập</Button></Link></div></section>
    </main>
    <footer className="landing-footer"><Link className="brand" href="/"><span className="brand-mark">G</span>Growup</Link><span>AI kiểm tra mức hiểu trên VLearn</span><span>Nhóm Growup · Lớp 3B</span></footer>
  </div>;
}

