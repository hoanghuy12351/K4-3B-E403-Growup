'use strict';

// CP2: team-authored source excerpts and question templates. No AI call.
const catalogue = [
  { id: 'q1', section: 'Nền tảng mô hình', title: 'Token — đơn vị văn bản', sourceId: 'GU-M01', source: 'Token là đơn vị văn bản mô hình xử lý. Tùy cách tách, token có thể là một từ, một phần của từ hoặc một ký tự. Một token không luôn tương ứng với một từ hoàn chỉnh.', prompt: 'Token có luôn tương ứng với một từ hoàn chỉnh không?', a: 'Có, mỗi token luôn là một từ hoàn chỉnh.', b: 'Không, token có thể là từ, phần của từ hoặc ký tự.', correct: 'b', criterion: 'Nhận ra token không luôn bằng một từ hoàn chỉnh.', correctCount: 7, partialCount: 1, wrongCount: 2, unknownCount: 1, needsExplanation: false },
  { id: 'q2', section: 'Nền tảng mô hình', title: 'Dự đoán token tiếp theo', sourceId: 'GU-M02', source: 'Mô hình ngôn ngữ tạo văn bản bằng cách dự đoán lần lượt token tiếp theo dựa trên ngữ cảnh. Cơ chế này khác việc chỉ lấy một câu trả lời lưu sẵn và chép nguyên văn.', prompt: 'Mô hình ngôn ngữ tạo câu trả lời chủ yếu bằng cách nào?', a: 'Tìm một câu trả lời đã lưu sẵn rồi chép nguyên văn.', b: 'Dự đoán lần lượt token tiếp theo dựa trên ngữ cảnh.', correct: 'b', criterion: 'Nêu đúng cơ chế dự đoán token tiếp theo dựa trên ngữ cảnh.', correctCount: 8, partialCount: 1, wrongCount: 1, unknownCount: 1, needsExplanation: false },
  { id: 'q3', section: 'Kiểm chứng thông tin', title: 'Tự tin không bảo đảm đúng', sourceId: 'GU-M03', source: 'Mô hình có thể tạo câu trả lời diễn đạt tự tin nhưng chứa thông tin sai. Giọng điệu không bảo đảm độ đúng. Khi cần kiểm chứng, phải đối chiếu với nguồn đáng tin.', prompt: 'AI trả lời rất tự tin. Ta có thể kết luận thông tin đúng không?', a: 'Có, tự tin nghĩa là mô hình biết chắc thông tin đúng.', b: 'Không, vẫn cần đối chiếu với nguồn đáng tin.', correct: 'b', criterion: 'Giải thích rằng tự tin không bảo đảm đúng và cần đối chiếu nguồn.', correctCount: 6, partialCount: 2, wrongCount: 2, unknownCount: 1, needsExplanation: true }
];
const state = { selected: catalogue.map(item => item.id), drafts: [], opened: false, scenario: 'normal', classSize: 16, answer: null, review: 'pending', decision: null };
const $ = id => document.getElementById(id);
const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const allApproved = () => state.drafts.length > 0 && state.drafts.every(item => item.approved);
const hasEdits = () => state.drafts.some(item => ['prompt', 'a', 'b', 'correct', 'criterion'].some(key => item[key] !== catalogue.find(source => source.id === item.id)[key]));

function clearRound() {
  state.opened = false; state.answer = null; state.review = 'pending'; state.decision = null;
  $('answer-form').reset(); $('answer-status').hidden = true; $('submit-answer').textContent = 'Gửi câu trả lời →';
  $('decision-form').reset(); $('teacher-note').value = '';
}

function renderSelection() {
  const sections = [...new Set(catalogue.map(item => item.section))];
  $('concept-selection').innerHTML = sections.map(section => `<div class="scope-section"><h3>${section}</h3>${catalogue.filter(item => item.section === section).map(item => `<label class="scope-choice"><input type="checkbox" data-concept="${item.id}" ${state.selected.includes(item.id) ? 'checked' : ''}><span><strong>${item.title}</strong><small>Đoạn nguồn mẫu ${item.sourceId} · một câu kiểm tra</small></span></label><details><summary>Đọc đoạn nguồn ${item.sourceId}</summary><p>${item.source}</p></details>`).join('')}</div>`).join('');
  $('concept-selection').querySelectorAll('[data-concept]').forEach(input => input.addEventListener('change', () => {
    state.selected = catalogue.filter(item => $('concept-selection').querySelector(`[data-concept="${item.id}"]`).checked).map(item => item.id);
    state.drafts = []; clearRound(); updateSelection();
  }));
  updateSelection();
}

function updateSelection() {
  const count = state.selected.length;
  $('selection-count').textContent = count ? `Đã chọn ${count} khái niệm → ${count} câu kiểm tra` : 'Chọn ít nhất một khái niệm để tạo kiểm tra';
  $('scope-summary').textContent = `${count} khái niệm · ${count} câu hỏi · khoảng ${Math.max(1, count)} phút`;
  $('create-check').disabled = count === 0;
}

function validateConfiguration() {
  if (!$('class-size').reportValidity()) return false;
  const size = Number($('class-size').value), scenario = $('scenario').value;
  if (scenario === 'normal' && size < 12 && !hasEdits()) {
    $('class-size').setCustomValidity('Tình huống có 11 phản hồi giả lập cần lớp ít nhất 12 người. Hoặc chọn tình huống chỉ có câu trả lời thử.');
    $('class-size').reportValidity(); return false;
  }
  state.classSize = size; state.scenario = scenario; return true;
}

function renderDrafts() {
  $('review-locked').hidden = state.drafts.length > 0; $('review-body').hidden = state.drafts.length === 0;
  $('question-drafts').innerHTML = state.drafts.map((item, index) => `<article class="card draft-card" data-draft="${item.id}"><div class="draft-heading"><h2>Câu ${index + 1} · ${item.title}</h2><span id="badge-${item.id}" class="pill ${item.approved ? '' : 'unapproved'}">${item.approved ? 'Đã duyệt' : 'Cần duyệt'}</span></div><div class="draft-source"><strong>Căn cứ · ${item.sourceId} · nhóm tự soạn</strong><p>${item.source}</p></div><label for="prompt-${item.id}">Nội dung câu ${index + 1}</label><textarea id="prompt-${item.id}" data-field="prompt" rows="2" maxlength="500" required>${escapeHtml(item.prompt)}</textarea><div class="editor-grid"><div><label for="a-${item.id}">Lựa chọn A · câu ${index + 1}</label><textarea id="a-${item.id}" data-field="a" rows="2" maxlength="400" required>${escapeHtml(item.a)}</textarea></div><div><label for="b-${item.id}">Lựa chọn B · câu ${index + 1}</label><textarea id="b-${item.id}" data-field="b" rows="2" maxlength="400" required>${escapeHtml(item.b)}</textarea></div></div><p class="field-note">Học viên luôn có thêm lựa chọn “Tôi chưa rõ”.</p><label for="correct-${item.id}">Đáp án đúng · câu ${index + 1}</label><select id="correct-${item.id}" data-field="correct"><option value="a" ${item.correct === 'a' ? 'selected' : ''}>Lựa chọn A</option><option value="b" ${item.correct === 'b' ? 'selected' : ''}>Lựa chọn B</option></select><label for="criterion-${item.id}">Tiêu chí đánh giá · câu ${index + 1}</label><textarea id="criterion-${item.id}" data-field="criterion" rows="2" maxlength="600" required>${escapeHtml(item.criterion)}</textarea><p class="field-note">${item.needsExplanation ? 'Có lời giải thích ngắn để giảng viên kiểm chứng mức hiểu.' : 'Chọn đúng chỉ là một tín hiệu, chưa chứng minh hiểu sâu.'}</p><label class="approve-choice"><input id="approve-${item.id}" type="checkbox" data-approve="${item.id}" ${item.approved ? 'checked' : ''}> Tôi đã kiểm tra và duyệt câu ${index + 1}, đáp án và căn cứ.</label></article>`).join('');
  $('question-drafts').querySelectorAll('[data-field]').forEach(input => input.addEventListener('input', () => {
    const item = state.drafts.find(draft => draft.id === input.closest('[data-draft]').dataset.draft);
    item[input.dataset.field] = input.value; item.approved = false; $('approve-' + item.id).checked = false;
    input.setCustomValidity(input.value.trim() ? '' : 'Nội dung không được để trống.');
    // Clear duplicate-choice validity when either choice is edited.
    if (['a', 'b'].includes(input.dataset.field)) $('b-' + item.id).setCustomValidity(item.b.trim() ? '' : 'Nội dung không được để trống.');
    clearRound(); updateApproval();
  }));
  $('question-drafts').querySelectorAll('[data-approve]').forEach(input => input.addEventListener('change', () => {
    const item = state.drafts.find(draft => draft.id === input.dataset.approve);
    if (!input.checked) { item.approved = false; clearRound(); updateApproval(); return; }
    const fields = [...input.closest('[data-draft]').querySelectorAll('[data-field]')];
    fields.forEach(field => field.setCustomValidity(field.value.trim() ? '' : 'Nội dung không được để trống.'));
    if (item.a.trim() === item.b.trim()) $('b-' + item.id).setCustomValidity('Hai lựa chọn cần khác nhau.');
    const invalid = fields.find(field => !field.reportValidity());
    input.checked = !invalid; item.approved = !invalid; updateApproval();
  }));
  updateApproval();
}

function updateApproval() {
  const count = state.drafts.filter(item => item.approved).length;
  $('approval-status').textContent = `Đã duyệt ${count}/${state.drafts.length} câu hỏi`; $('open-check').disabled = !allApproved();
  $('approval-note').textContent = hasEdits() ? 'Câu hỏi đã được sửa: chỉ dùng câu trả lời thử, không ghép phản hồi giả lập của bộ câu cũ.' : 'Chỉ mở kiểm tra khi tất cả câu hỏi đã được duyệt.';
  state.drafts.forEach(item => { const badge = $('badge-' + item.id); if (badge) { badge.textContent = item.approved ? 'Đã duyệt' : 'Cần duyệt'; badge.classList.toggle('unapproved', !item.approved); } });
}

function renderStudent() {
  $('student-locked').hidden = state.opened; $('answer-form').hidden = !state.opened;
  if (!state.opened) return;
  $('student-questions').innerHTML = state.drafts.map((item, index) => `<fieldset><legend><span class="question-index">0${index + 1}</span> ${escapeHtml(item.prompt)}</legend>${['a', 'b'].map(option => `<label class="answer"><input type="radio" name="${item.id}" value="${option}" ${state.answer?.[item.id] === option ? 'checked' : ''} required> ${escapeHtml(item[option])}</label>`).join('')}<label class="answer"><input type="radio" name="${item.id}" value="unknown" ${state.answer?.[item.id] === 'unknown' ? 'checked' : ''}> Tôi chưa rõ.</label>${item.needsExplanation ? `<label for="explanation">Giải thích ngắn lý do bạn chọn (không bắt buộc)</label><textarea id="explanation" name="explanation" rows="3" maxlength="600" placeholder="Viết 1–2 câu bằng lời của bạn…">${escapeHtml(state.answer?.explanation || '')}</textarea><p class="field-note">Ở CP2, giảng viên xem lời giải thích; bản mẫu chưa tự đánh giá ý nghĩa văn bản.</p>` : ''}</fieldset>`).join('');
}

function summarize() {
  const useFixture = state.opened && state.scenario === 'normal' && !hasEdits();
  const useAnswer = state.opened && state.answer && ['normal', 'sparse'].includes(state.scenario);
  const concepts = state.drafts.map(item => {
    const counts = { correct: useFixture ? item.correctCount : 0, partial: useFixture ? item.partialCount : 0, wrong: useFixture ? item.wrongCount : 0, unknown: useFixture ? item.unknownCount : 0 };
    if (useAnswer) { const choice = state.answer[item.id]; counts[choice === 'unknown' ? 'unknown' : choice !== item.correct ? 'wrong' : item.needsExplanation && state.review !== 'confirmed' ? 'partial' : 'correct']++; }
    return { ...item, ...counts };
  });
  const total = state.opened && state.scenario !== 'failure' ? (useFixture ? 11 : 0) + (useAnswer ? 1 : 0) : 0;
  return { concepts, total, participation: Math.round(total / state.classSize * 100), insufficient: total / state.classSize < .5, failure: state.scenario === 'failure' };
}

function showScreen(name) {
  document.querySelectorAll('.screen').forEach(screen => { screen.hidden = screen.id !== name; });
  document.querySelectorAll('.step').forEach(button => { button.classList.toggle('active', button.dataset.step === name); if (button.dataset.step === name) button.setAttribute('aria-current', 'step'); else button.removeAttribute('aria-current'); });
  if (name === 'review') renderDrafts(); if (name === 'student') renderStudent(); if (name === 'report') renderReport(); if (name === 'decision') renderDecision();
  $('main').focus({ preventScroll: true }); window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderReport() {
  $('report-scenario').value = state.scenario; const summary = summarize(); $('to-decision').disabled = !state.opened;
  if (!state.opened) { $('report-content').innerHTML = '<article class="card empty-state"><h2>Chưa có lượt kiểm tra đã duyệt</h2><p>Chọn phạm vi, duyệt câu hỏi rồi mở kiểm tra.</p><button class="primary" data-go="prepare">Chuẩn bị kiểm tra</button></article>'; return; }
  if (summary.failure) { $('report-content').innerHTML = '<div class="callout error"><strong>Chưa thể tổng hợp kết quả — tình huống lỗi giả lập</strong><p>Không hiển thị kết quả cũ như thể mới phân tích. Câu trả lời thử vẫn còn trong lượt hiện tại.</p></div><article class="card empty-state"><h2>Thử lại hoặc xem câu trả lời</h2><p>Chọn tình huống khác rồi bấm “Tổng hợp lại” để phục hồi.</p><button class="secondary" data-go="student">Xem câu trả lời thử</button></article>'; return; }
  let html = `<div class="metrics"><div class="metric"><span class="value">${summary.total}/${state.classSize}</span><span class="caption">Học viên đã trả lời · dữ liệu mẫu</span></div><div class="metric"><span class="value">${summary.participation}%</span><span class="caption">Tỷ lệ tham gia, không phải tỷ lệ hiểu</span></div><div class="metric"><span class="value">${Math.max(0, state.classSize - summary.total)}</span><span class="caption">Chưa trả lời · chưa biết mức hiểu</span></div></div>`;
  if (hasEdits()) html += '<div class="callout"><strong>Đang dùng câu hỏi giảng viên đã sửa</strong><p>Không ghép 11 phản hồi giả lập của bộ câu cũ. Chỉ tổng hợp câu trả lời thử trong lượt này.</p></div>';
  if (!summary.total) { $('report-content').innerHTML = html + '<article class="card empty-state"><h2>Chưa có dữ liệu đánh giá</h2><p>Mời học viên trả lời. Sự im lặng không cho biết lớp đã hiểu hay chưa.</p></article>'; return; }
  html += summary.insufficient ? '<div class="callout warning"><strong>Chưa đủ dữ liệu để nhận xét chung về lớp</strong><p>Dưới 50% lớp mẫu đã trả lời. Các số dưới đây chỉ mô tả người đã phản hồi.</p></div>' : '<div class="callout"><strong>Có thể xem xét chỗ cần giảng lại</strong><p>Kết quả chỉ mô tả người đã trả lời. Xem bằng chứng và phần chưa chắc trước khi quyết định.</p></div>';
  html += '<div class="report-cards">';
  summary.concepts.forEach((item, index) => {
    const percent = Math.round(item.correct / summary.total * 100);
    html += `<article class="card report-card"><span class="tag">KHÁI NIỆM 0${index + 1}</span><h3>${item.title}</h3><span class="score">${percent}% <small>đáp ứng tiêu chí mẫu</small></span><div class="bar"><span style="width:${percent}%"></span></div><div class="breakdown">Đáp ứng: ${item.correct}/${summary.total}<br>Cần xem thêm: ${item.partial}/${summary.total}<br>Hiểu lầm theo đáp án: ${item.wrong}/${summary.total}<br>Tự báo chưa rõ: ${item.unknown}/${summary.total}</div><details><summary>Xem bằng chứng và tiêu chí</summary>`;
    if (state.scenario === 'normal' && !hasEdits()) html += `<p>Ví dụ phản hồi giả lập:</p><blockquote>${escapeHtml(item.a)}</blockquote>`;
    if (state.answer) html += `<p>Câu trả lời thử: <strong>${escapeHtml(state.answer[item.id] === 'unknown' ? 'Tôi chưa rõ' : item[state.answer[item.id]])}</strong>.</p>`;
    html += `<p><strong>Tiêu chí đã duyệt:</strong> ${escapeHtml(item.criterion)}</p><p><strong>Căn cứ ${item.sourceId}:</strong> ${item.source}</p><p class="source-note">Nguồn nhóm tự soạn. CP3 cần gắn tài liệu bài học đã kiểm chứng. Chọn đúng chưa đủ chứng minh hiểu sâu.</p></details></article>`;
  });
  html += '</div>'; const explanationQuestion = state.drafts.find(item => item.needsExplanation);
  if (state.answer && explanationQuestion) {
    html += `<article class="card review-card"><h3>Lời giải thích của học viên thử</h3><blockquote>${escapeHtml(state.answer.explanation || 'Chưa nhập lời giải thích.')}</blockquote><p class="field-note">Ẩn danh. Văn bản chưa được AI đánh giá ở CP2.</p>`;
    if (state.answer[explanationQuestion.id] === explanationQuestion.correct) html += `<label for="review-answer">Giảng viên kiểm chứng lời giải thích</label><select id="review-answer"><option value="pending" ${state.review === 'pending' ? 'selected' : ''}>Chưa xác nhận hiểu thật — cần xem thêm</option><option value="confirmed" ${state.review === 'confirmed' ? 'selected' : ''}>Giảng viên xác nhận lời giải thích đáp ứng tiêu chí</option></select>`;
    html += '</article>';
  }
  $('report-content').innerHTML = html;
  if ($('review-answer')) $('review-answer').addEventListener('change', event => { state.review = event.target.value; state.decision = null; renderReport(); });
}

function renderDecision() {
  const summary = summarize(); $('decision-form').hidden = !state.opened; $('decision-saved').hidden = !state.decision;
  $('decision-context').textContent = !state.opened ? 'Chưa mở lượt kiểm tra đã duyệt.' : summary.failure ? 'Tổng hợp đang lỗi. Xem câu trả lời hoặc thử lại trước khi nhận xét.' : !summary.total ? 'Chưa có phản hồi. Mời học viên trả lời trước khi kết luận.' : summary.insufficient ? `Mới có ${summary.total}/${state.classSize} người trả lời. Chưa đủ dữ liệu để nhận xét chung về lớp.` : `Đã có ${summary.total}/${state.classSize} người trả lời. Xem hiểu lầm và bằng chứng ở từng khái niệm đã chọn.`;
  if (state.decision) $('decision-saved').textContent = `Đã lưu trong lượt thử: ${state.decision.action}.${state.decision.note ? ' Ghi chú: ' + state.decision.note : ''} Có thể mở lượt thử mới để kiểm tra lại.`;
}

document.addEventListener('click', event => { const button = event.target.closest('[data-step], [data-go]'); if (button) showScreen(button.dataset.step || button.dataset.go); });
document.querySelector('.brand').addEventListener('click', event => { event.preventDefault(); showScreen('prepare'); });
$('create-check').addEventListener('click', () => {
  if (!state.selected.length || !validateConfiguration()) return;
  clearRound(); state.drafts = catalogue.filter(item => state.selected.includes(item.id)).map(item => ({ ...item, approved: false })); showScreen('review');
});
$('question-review-form').addEventListener('submit', event => event.preventDefault());
$('open-check').addEventListener('click', () => {
  if (!allApproved() || !$('question-review-form').reportValidity() || !validateConfiguration()) return;
  clearRound(); if (hasEdits() && state.scenario === 'normal') state.scenario = 'sparse'; state.opened = true; showScreen('student');
});
$('class-size').addEventListener('input', () => { $('class-size').setCustomValidity(''); clearRound(); });
$('scenario').addEventListener('change', () => { $('class-size').setCustomValidity(''); clearRound(); });
$('fill-example').addEventListener('click', () => {
  state.drafts.forEach((item, index) => { const option = index === 0 ? (item.correct === 'a' ? 'b' : 'a') : item.correct; document.querySelector(`input[name="${item.id}"][value="${option}"]`).checked = true; });
  if ($('explanation')) $('explanation').value = 'Giọng điệu tự tin không bảo đảm thông tin đúng, nên cần đối chiếu với nguồn đáng tin.';
});
$('answer-form').addEventListener('submit', event => {
  event.preventDefault(); if (!state.opened || !allApproved()) return;
  const form = new FormData(event.target); state.answer = { explanation: String(form.get('explanation') || '').trim() };
  state.drafts.forEach(item => { state.answer[item.id] = form.get(item.id); }); state.review = 'pending'; state.decision = null;
  $('answer-status').hidden = false; $('answer-status').textContent = 'Đã nhận câu trả lời. Sửa và gửi lại không được đếm thành học viên mới.';
  $('submit-answer').textContent = 'Cập nhật câu trả lời →'; showScreen('report');
});
$('refresh-report').addEventListener('click', () => { const selected = $('report-scenario').value; state.scenario = selected === 'normal' && (state.classSize < 12 || hasEdits()) ? 'sparse' : selected; state.decision = null; renderReport(); });
$('to-decision').addEventListener('click', () => showScreen('decision'));
$('decision-form').addEventListener('submit', event => { event.preventDefault(); if (!state.opened) return; state.decision = { action: new FormData(event.target).get('decision'), note: $('teacher-note').value.trim() }; renderDecision(); });
$('reset-demo').addEventListener('click', () => { clearRound(); Object.assign(state, { selected: catalogue.map(item => item.id), drafts: [], scenario: 'normal', classSize: 16 }); $('class-size').value = '16'; $('class-size').setCustomValidity(''); $('scenario').value = 'normal'; renderSelection(); showScreen('prepare'); });
renderSelection();
