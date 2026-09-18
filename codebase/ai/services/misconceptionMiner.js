'use strict';

function normalize(value) { return String(value || '').replace(/\s+/g, ' ').trim(); }
function slug(value) { return normalize(value).toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-|-$/g, '') || 'concept'; }
function excerpt(value, maximum = 220) { const text = normalize(value); return text.length > maximum ? `${text.slice(0, maximum - 1)}…` : text; }

function classifyQuestion(text) {
  const value = normalize(text).toLocaleLowerCase();
  if (/(difference|different|distinguish|versus|\bvs\b|khác|phân biệt)/u.test(value)) return 'distinction';
  if (/(what is|meaning|define|là gì|nghĩa là|định nghĩa)/u.test(value)) return 'definition';
  if (/(how|use|apply|cách|dùng|áp dụng)/u.test(value)) return 'application';
  return 'general';
}

const STATEMENTS = Object.freeze({
  distinction: concept => `Possible historical confusion: ${concept} may be conflated with a related concept.`,
  definition: concept => `Possible historical confusion: the definition or scope of ${concept} may be unclear.`,
  application: concept => `Possible historical confusion: when or how to apply ${concept} may be unclear.`,
  general: concept => `Possible historical question pattern: students requested clarification about ${concept}.`
});

/** Group keyword-level question patterns while retaining short, auditable evidence excerpts. */
function mineMisconceptions({ concepts = [], historicalQuestions = [] } = {}) {
  const groups = new Map();
  for (const concept of concepts.map(normalize).filter(Boolean)) {
    const conceptTerms = concept.toLocaleLowerCase().match(/[\p{L}\p{N}]{2,}/gu) || [];
    for (const question of historicalQuestions) {
      const text = normalize(question.studentQuestion);
      const haystack = text.toLocaleLowerCase();
      if (!conceptTerms.some(term => haystack.includes(term))) continue;
      const category = classifyQuestion(text);
      const key = `${slug(concept)}-${category}`;
      if (!groups.has(key)) groups.set(key, { concept, category, evidence: [] });
      const evidence = groups.get(key).evidence;
      if (!evidence.some(item => item.turnId === question.turnId) && evidence.length < 5) evidence.push({ turnId: question.turnId, excerpt: excerpt(text) });
    }
  }
  return {
    misconceptions: [...groups.entries()].map(([key, group], index) => ({
      id: `M${String(index + 1).padStart(3, '0')}-${key}`,
      concept: group.concept,
      statement: STATEMENTS[group.category](group.concept),
      evidence: group.evidence,
      evidenceCount: group.evidence.length,
      confidence: Number(Math.min(0.8, 0.35 + group.evidence.length * 0.1).toFixed(2))
    }))
  };
}

module.exports = { mineMisconceptions };
