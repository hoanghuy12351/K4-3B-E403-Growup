'use strict';

// CP2: synthetic fixtures and explicit answer-key rules. No AI call.
const fixture = {
  responses: 11,
  concepts: [
    { title: 'Token không luôn bằng một từ', correct: 7, partial: 1, wrong: 2, unknown: 1, quote: 'Mỗi token là một từ đầy đủ.', expected: 'Token có thể là từ, phần của từ hoặc ký tự.' },
    { title: 'Dự đoán token tiếp theo', correct: 8, partial: 1, wrong: 1, unknown: 1, quote: 'Mô hình lấy nguyên câu trả lời có sẵn.', expected: 'Mô hình dự đoán lần lượt token tiếp theo dựa trên ngữ cảnh.' },
    { title: 'Tự tin không bảo đảm đúng', correct: 6, partial: 2, wrong: 2, unknown: 1, quote: 'Nếu AI tự tin thì chắc thông tin đúng.', expected: 'Cần đối chiếu thông tin với nguồn đáng tin, dù câu trả lời rất tự tin.' }
  ]
};
const state = { opened: false, scenario: 'normal', classSize: 16, answer: null, review: 'pending', decision: null };
const $ = id => document.getElementById(id);
const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));

function summarize() {
  const useFixture = state.scenario === 'normal';
  const useAnswer = state.opened && state.answer && ['normal', 'sparse'].includes(state.scenario);
  const concepts = fixture.concepts.map((item, index) => {
    const counts = { correct: useFixture ? item.correct : 0, partial: useFixture ? item.partial : 0, wrong: useFixture ? item.wrong : 0, unknown: useFixture ? item.unknown : 0 };
    if (useAnswer) {
      const response = state.answer['q' + (index + 1)];
      const category = index === 2 && response === 'correct' ? (state.review === 'confirmed' ? 'correct' : 'partial') : response === 'correct' ? 'correct' : response === 'wrong' ? 'wrong' : 'unknown';
      counts[category]++;
    }
    return { ...item, ...counts };
  });
  const total = state.opened && state.scenario !== 'failure' ? (useFixture ? fixture.responses : 0) + (useAnswer ? 1 : 0) : 0;
  const participation = Math.round(total / state.classSize * 100);
  return { concepts, total, participation, insufficient: total / state.classSize < .5, failure: state.scenario === 'failure' };
}

function showScreen(name) {
  document.querySelectorAll('.screen').forEach(screen => { screen.hidden = screen.id !== name; });
  document.querySelectorAll('.step').forEach(button => {
    button.classList.toggle('active', button.dataset.step === name);
    if (button.dataset.step === name) button.setAttribute('aria-current', 'step'); else button.removeAttribute('aria-current');
  });
  if (name === 'student') {
    $('student-locked').hidden = state.opened;
    $('answer-form').hidden = !state.opened;
  }
  if (name === 'report') renderReport();
  if (name === 'decision') renderDecision();
  $('main').focus({ preventScroll: true });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderReport() {
  $('report-scenario').value = state.scenario;
  const summary = summarize();
  $('to-decision').disabled = !state.opened;
  if (!state.opened) {
    $('report-content').innerHTML = '<article class="card empty-state"><h2>Chưa có lượt kiểm tra</h2><p>Về bước chuẩn bị và mở kiểm tra để thử luồng.</p><button class="primary" data-go="prepare">Chuẩn bị kiểm tra</button></article>';
    return;
  }
  if (summary.failure) {
    $('report-content').innerHTML = '<div class="callout error"><strong>Chưa thể tổng hợp kết quả — tình huống lỗi giả lập</strong><p>Không hiển thị kết quả cũ như thể mới phân tích. Câu trả lời thử của bạn vẫn còn trong lượt hiện tại.</p></div><article class="card empty-state"><div class="empty-icon">↻</div><h2>Thử lại hoặc xem câu trả lời</h2><p>Chọn tình huống khác rồi bấm “Tổng hợp lại” để phục hồi. Bạn cũng có thể xem câu trả lời và tự quyết định cách dạy tiếp.</p><button class="secondary" data-go="student">Xem câu trả lời thử</button></article>';
    return;
  }
  const unanswered = Math.max(0, state.classSize - summary.total);
  let html = `<div class="metrics"><div class="metric"><span class="value">${summary.total}/${state.classSize}</span><span class="caption">Học viên đã trả lời · dữ liệu mẫu</span></div><div class="metric"><span class="value">${summary.participation}%</span><span class="caption">Tỷ lệ tham gia, không phải tỷ lệ hiểu</span></div><div class="metric"><span class="value">${unanswered}</span><span class="caption">Chưa trả lời · chưa biết mức hiểu</span></div></div>`;
  if (summary.total === 0) {
    $('report-content').innerHTML = html + '<article class="card empty-state"><div class="empty-icon">○</div><h2>Chưa có dữ liệu đánh giá</h2><p>Mời học viên trả lời hoặc kiểm tra họ có truy cập được câu hỏi không. Sự im lặng không cho biết lớp đã hiểu hay chưa.</p></article>';
    return;
  }
  html += summary.insufficient
    ? '<div class="callout warning"><strong>Chưa đủ dữ liệu để nhận xét chung về lớp</strong><p>Dưới 50% lớp mẫu đã trả lời. Các số dưới đây chỉ mô tả người đã phản hồi; nên mời thêm học viên trả lời.</p></div>'
    : '<div class="callout"><strong>Có thể xem xét chỗ cần giảng lại</strong><p>Kết quả chỉ mô tả người đã trả lời. Kiểm tra bằng chứng và phần chưa chắc trước khi quyết định cho lớp đi tiếp.</p></div>';
  html += '<div class="report-cards">';
  summary.concepts.forEach((concept, index) => {
    const percent = Math.round(concept.correct / summary.total * 100);
    html += `<article class="card report-card"><span class="tag">KHÁI NIỆM 0${index + 1}</span><h3>${concept.title}</h3><span class="score">${percent}% <small>đáp ứng tiêu chí mẫu</small></span><div class="bar"><span style="width:${percent}%"></span></div><div class="breakdown">Đáp ứng: ${concept.correct}/${summary.total}<br>Cần xem thêm: ${concept.partial}/${summary.total}<br>Hiểu lầm theo đáp án: ${concept.wrong}/${summary.total}<br>Tự báo chưa rõ: ${concept.unknown}/${summary.total}</div><details><summary>Xem bằng chứng và tiêu chí</summary>`;
    if (state.scenario === 'normal') html += `<p>Ví dụ từ phản hồi giả lập:</p><blockquote>${concept.quote}</blockquote>`;
    if (state.answer) html += `<p>Câu trả lời thử của bạn: <strong>${({ correct: 'Chọn đáp án đúng', wrong: 'Chọn đáp án chứa hiểu lầm', unknown: 'Tôi chưa rõ' })[state.answer['q' + (index + 1)]]}</strong>.</p>`;
    html += `<p><strong>Tiêu chí mẫu:</strong> ${concept.expected}</p><p class="source-note">Nội dung nhóm tự soạn, chưa trích tài liệu khóa học. CP3 cần gắn nguồn đã kiểm chứng. Chọn đúng đáp án chưa đủ chứng minh hiểu sâu.</p></details></article>`;
  });
  html += '</div>';
  if (state.answer) {
    html += `<article class="card review-card"><h3>Lời giải thích của học viên thử</h3><blockquote>${state.answer.explanation ? escapeHtml(state.answer.explanation) : 'Chưa nhập lời giải thích.'}</blockquote><p class="field-note">Ẩn danh trong màn hình giảng viên. Phân loại văn bản chưa được AI thực hiện ở bản mẫu.</p>`;
    if (state.answer.q3 === 'correct') html += `<label for="review-answer">Giảng viên xem lại câu 3</label><select id="review-answer"><option value="pending" ${state.review === 'pending' ? 'selected' : ''}>Chưa xác nhận hiểu thật — cần xem thêm</option><option value="confirmed" ${state.review === 'confirmed' ? 'selected' : ''}>Giảng viên xác nhận lời giải thích đáp ứng tiêu chí</option></select>`;
    html += '</article>';
  }
  $('report-content').innerHTML = html;
  const review = $('review-answer');
  if (review) review.addEventListener('change', event => { state.review = event.target.value; renderReport(); });
}

function renderDecision() {
  const summary = summarize();
  $('decision-form').hidden = !state.opened;
  $('decision-saved').hidden = !state.decision;
  $('decision-context').textContent = !state.opened ? 'Chưa mở lượt kiểm tra. Về bước chuẩn bị trước.' : summary.failure ? 'Tổng hợp đang lỗi. Xem trực tiếp câu trả lời hoặc thử tổng hợp lại trước khi nhận xét mức hiểu.' : summary.total === 0 ? 'Chưa có phản hồi. Nên mời học viên trả lời trước khi đưa ra nhận xét.' : summary.insufficient ? `Mới có ${summary.total}/${state.classSize} người trả lời. Chưa đủ dữ liệu để nhận xét chung về lớp.` : `Đã có ${summary.total}/${state.classSize} người trả lời. Bảng kết quả là dữ liệu minh họa; hãy xem hiểu lầm và bằng chứng ở từng khái niệm.`;
  if (state.decision) $('decision-saved').textContent = `Đã lưu trong lượt thử: ${state.decision.action}.${state.decision.note ? ' Ghi chú: ' + state.decision.note : ''} Bạn có thể mở một lượt thử mới để minh họa bước kiểm tra lại.`;
}

document.addEventListener('click', event => {
  const step = event.target.closest('[data-step]');
  const link = event.target.closest('[data-go]');
  if (step) showScreen(step.dataset.step);
  if (link) showScreen(link.dataset.go);
});
document.querySelector('.brand').addEventListener('click', event => { event.preventDefault(); showScreen('prepare'); });
$('open-check').addEventListener('click', () => {
  if (!$('class-size').reportValidity()) return;
  const size = Number($('class-size').value);
  const scenario = $('scenario').value;
  if (scenario === 'normal' && size < fixture.responses + 1) {
    $('class-size').setCustomValidity('Tình huống có 11 phản hồi giả lập cần lớp ít nhất 12 người. Hoặc chọn tình huống chỉ có câu trả lời thử.');
    $('class-size').reportValidity();
    return;
  }
  state.opened = true; state.classSize = size; state.scenario = scenario;
  state.answer = null; state.review = 'pending'; state.decision = null;
  $('answer-form').reset(); $('answer-status').hidden = true; $('submit-answer').textContent = 'Gửi câu trả lời →';
  $('decision-form').reset(); $('teacher-note').value = '';
  showScreen('student');
});
$('class-size').addEventListener('input', () => $('class-size').setCustomValidity(''));
$('scenario').addEventListener('change', () => $('class-size').setCustomValidity(''));
$('fill-example').addEventListener('click', () => {
  document.querySelector('input[name="q1"][value="wrong"]').checked = true;
  document.querySelector('input[name="q2"][value="correct"]').checked = true;
  document.querySelector('input[name="q3"][value="correct"]').checked = true;
  $('explanation').value = 'Câu trả lời nghe tự tin vẫn có thể sai, nên cần kiểm tra với nguồn đáng tin.';
});
$('answer-form').addEventListener('submit', event => {
  event.preventDefault();
  if (!state.opened) return;
  const form = new FormData(event.target);
  state.answer = { q1: form.get('q1'), q2: form.get('q2'), q3: form.get('q3'), explanation: form.get('explanation').trim() };
  state.review = 'pending'; state.decision = null;
  $('answer-status').hidden = false;
  $('answer-status').textContent = 'Đã nhận câu trả lời trong lượt thử. Bạn có thể sửa và gửi lại; bản mẫu không đếm thành học viên mới.';
  $('submit-answer').textContent = 'Cập nhật câu trả lời →';
  showScreen('report');
});
$('refresh-report').addEventListener('click', () => {
  const selected = $('report-scenario').value;
  state.scenario = selected === 'normal' && state.classSize < fixture.responses + 1 ? 'sparse' : selected;
  state.decision = null;
  renderReport();
});
$('to-decision').addEventListener('click', () => showScreen('decision'));
$('decision-form').addEventListener('submit', event => {
  event.preventDefault();
  if (!state.opened) return;
  state.decision = { action: new FormData(event.target).get('decision'), note: $('teacher-note').value.trim() };
  renderDecision();
});
$('reset-demo').addEventListener('click', () => {
  Object.assign(state, { opened: false, scenario: 'normal', classSize: 16, answer: null, review: 'pending', decision: null });
  $('answer-form').reset(); $('decision-form').reset(); $('teacher-note').value = '';
  $('class-size').value = '16'; $('class-size').setCustomValidity(''); $('scenario').value = 'normal';
  $('answer-status').hidden = true; $('submit-answer').textContent = 'Gửi câu trả lời →';
  showScreen('prepare');
});
