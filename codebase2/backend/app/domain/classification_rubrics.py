"""Server-owned rubrics distilled from the approved slide/transcript sources."""

from app.domain.classification import ConceptRubric, UnknownConceptError


def _rubric(question_test_id: str, concept_id: str, question: str, evidence: tuple[str, ...], refs: tuple[str, ...], misconceptions: tuple[tuple[str, str], ...] = (), citation: str = "Use every directly relevant source reference.", review: str = "Escalate only when the supplied sources are conflicting or insufficient.") -> ConceptRubric:
    return ConceptRubric(question_test_id, concept_id, question, evidence, refs, misconceptions, citation, review)


RUBRICS = {
    ("QGEN-01", "token"): _rubric(
        "QGEN-01", "token", "Token là gì và vì sao không nên đồng nhất token với một từ?",
        ("Token là mảnh/đơn vị văn bản.", "Một từ có thể gồm nhiều token."),
        ("d1-slide:p13", "T04-049", "T06-134", "T06-135"),
        (("token_equals_word", "Khẳng định một token luôn bằng đúng một từ."),),
        "For correct/partial evidence use all four refs. For token_equals_word use only d1-slide:p13 and T04-049.",
    ),
    ("QGEN-01", "next_token_prediction"): _rubric(
        "QGEN-01", "next_token_prediction", "Mô tả ngắn vòng lặp LLM dùng để sinh một đoạn văn bản.",
        ("Dự đoán token tiếp theo.", "Nối token vào chuỗi, cập nhật context và lặp lại."),
        ("T04-047", "T06-136", "T06-137"),
    ),
    ("QGEN-01", "context_window"): _rubric(
        "QGEN-01", "context_window", "Context window là gì và một giới hạn của nó là gì?",
        ("Lượng thông tin model thấy trong một lần.", "Quá dài có thể tốn chi phí và bỏ sót thông tin."),
        ("d1-slide:p14", "T04-051", "T04-052"),
    ),
    ("QGEN-02", "attention"): _rubric(
        "QGEN-02", "attention", "Attention giúp token sử dụng ngữ cảnh như thế nào?",
        ("Đánh trọng số mức độ liên quan.", "Kết nối token theo ngữ cảnh."),
        ("d1-slide:p15", "T04-054", "T04-055", "T06-130"),
        (("attention_only_adjacent_sequential", "Cho rằng attention chỉ đọc tuần tự và chỉ nhìn token kề bên."),),
    ),
    ("QGEN-02", "long_context_limit"): _rubric(
        "QGEN-02", "long_context_limit", "Tại sao context dài hơn không đồng nghĩa kết quả luôn tốt hơn?",
        ("Có thể loãng attention hoặc bỏ sót thông tin.", "Tăng chi phí và độ trễ."),
        ("d1-slide:p14-p16", "d1-slide:p14", "T04-051", "T04-052", "T04-053", "T06-127"),
        (),
        "For a supported answer use d1-slide:p14-p16,T04-051,T04-052,T04-053. For the disputed parallel-processing/never-forgets claim use T06-127,d1-slide:p14,T04-052,T04-053.",
        "The sources phrase parallel processing and long-context limits inconsistently. The absolute claim that a Transformer never forgets because it processes in parallel must be teacher_review, not mechanically marked wrong.",
    ),
    ("QGEN-02", "hallucination_and_grounding"): _rubric(
        "QGEN-02", "hallucination_and_grounding", "Vì sao LLM có thể trả lời hợp lý nhưng sai, và nên giảm rủi ro thế nào?",
        ("LLM tối ưu dự đoán token, không bảo đảm sự thật.", "Cần retrieval/RAG, citation, eval hoặc human review theo rủi ro."),
        ("d1-slide:p20", "T04-048", "T06-138", "T06-149"),
        (("hallucination_is_temporary_bug", "Coi hallucination chỉ là bug tạm thời."), ("bigger_model_needs_no_grounding", "Cho rằng model lớn không cần grounding/dẫn nguồn.")),
    ),
    ("QGEN-03", "diverge_converge"): _rubric(
        "QGEN-03", "diverge_converge", "Vì sao nên mở rộng nhiều ứng viên vấn đề trước khi chọn?",
        ("Giảm nguy cơ nhảy vào vấn đề/giải pháp đầu tiên.", "Tránh bỏ sót ứng viên tốt hơn."),
        ("T01-049", "T01-069", "T01-070"),
    ),
    ("QGEN-03", "problem_statement_fields"): _rubric(
        "QGEN-03", "problem_statement_fields", "Nêu các thành phần cốt lõi của problem statement có thể đo và kiểm chứng.",
        ("Actor, workflow, bottleneck, impact, success metric và boundary."),
        ("d2-slide:p27", "d2-slide:p27-p29", "T05-145", "T05-146"),
        (("solution_disguised_as_problem", "Mô tả solution thay cho problem."), ("scope_too_broad", "Phạm vi quá rộng, không kiểm chứng được."), ("missing_impact_metric_boundary", "Thiếu impact, success metric và boundary.")),
        "For a complete field list use d2-slide:p27,T05-145. For solution-shaped/problem-scope errors use d2-slide:p27-p29,T05-145,T05-146.",
    ),
    ("QGEN-03", "impact_and_success_metric"): _rubric(
        "QGEN-03", "impact_and_success_metric", "Impact và success metric giúp nhóm ra quyết định thế nào?",
        ("Lượng hóa giá trị và ưu tiên bài toán.", "Cho biết khi nào giải pháp thành công."),
        ("T01-074", "T01-078", "T05-145"),
    ),
    ("QGEN-04", "automation_vs_augmentation"): _rubric(
        "QGEN-04", "automation_vs_augmentation", "Automate và augment khác nhau ở vai trò con người thế nào?",
        ("Automate là AI làm thay.", "Augment là AI hỗ trợ và con người giữ quyền quyết định."),
        ("d2-slide:p17", "T02-032", "T02-034"),
    ),
    ("QGEN-04", "cost_of_error"): _rubric(
        "QGEN-04", "cost_of_error", "Khi đánh giá sai có hậu quả cao nên chọn mức automation nào?",
        ("Nghiêng về augmentation/conditional.", "Giữ human oversight vì hậu quả sai cao."),
        ("d2-slide:p17", "T02-034"),
    ),
    ("QGEN-04", "rule_workflow_agent"): _rubric(
        "QGEN-04", "rule_workflow_agent", "Rule, workflow và agent khác nhau thế nào?",
        ("Rule cho logic cố định.", "Workflow cho bước/nhánh rõ.", "Agent cho nhiều bước, tool và trạng thái động."),
        ("d2-slide:p17-p21", "T02-033", "T02-038", "T02-039"),
        (("agent_always_best", "Cho rằng agent luôn là lựa chọn tốt nhất."), ("agent_equals_full_automation", "Đồng nhất agent với automate 100%.")),
    ),
    ("QGEN-05", "learning_metric"): _rubric(
        "QGEN-05", "learning_metric", "Vì sao user quay lại chưa đủ để kết luận học tốt hơn?",
        ("Usage/retention chỉ có thể là metric trung gian.", "Cần learning outcome như quiz, làm bài hoặc giải thích lại."),
        ("T02-021", "T02-023", "T02-024", "T02-025"),
        (("retention_equals_learning", "Đồng nhất retention/usage với kết quả học tập."),),
    ),
    ("QGEN-05", "precision_recall_cost"): _rubric(
        "QGEN-05", "precision_recall_cost", "False positive và false negative gây hậu quả khác nhau thế nào?",
        ("FP có thể làm giảng lại không cần thiết.", "FN có thể bỏ sót kiến thức chưa nắm.", "Cân bằng theo chi phí lỗi."),
        ("d2-slide:p22-p23",),
    ),
    ("QGEN-05", "operating_scope_and_fallback"): _rubric(
        "QGEN-05", "operating_scope_and_fallback", "Hệ thống nên làm gì khi phản hồi ít, mơ hồ hoặc nguồn không đủ?",
        ("Nói rõ chưa đủ dữ liệu.", "Hỏi lại/chuyển người và không tự kết luận."),
        ("d2-slide:p25-p28", "T03-097", "T03-105", "T03-107", "T03-127", "T03-137"),
    ),
}


def get_rubric(question_test_id: str, concept_id: str) -> ConceptRubric:
    try:
        return RUBRICS[(question_test_id, concept_id)]
    except KeyError as error:
        raise UnknownConceptError(
            f"Unsupported question/concept pair: {question_test_id}/{concept_id}"
        ) from error
