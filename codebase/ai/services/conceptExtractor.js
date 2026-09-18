'use strict';

const STOP_WORDS = new Set(['about', 'after', 'also', 'and', 'are', 'based', 'before', 'being', 'between', 'can', 'concept', 'context', 'does', 'for', 'from', 'into', 'lesson', 'more', 'must', 'not', 'that', 'the', 'this', 'through', 'using', 'with', 'what', 'which', 'your', 'các', 'cho', 'của', 'được', 'khái', 'là', 'một', 'này', 'những', 'trong', 'và', 'về']);

function clean(value) { return String(value || '').replace(/\s+/g, ' ').trim(); }
function titleCase(value) { return value.replace(/\b\p{L}/gu, character => character.toLocaleUpperCase()); }

/** Deterministically derive a small teaching context; it can later be replaced by an LLM implementation. */
function extractConcepts({ sourceText = '', title = '', sourceId = '' } = {}) {
  const text = clean(sourceText);
  const heading = clean(title);
  if (!text && !heading) throw new Error('Concept extraction requires sourceText or title.');
  const candidates = [];
  if (heading) candidates.push(heading);
  const frequency = new Map();
  for (const word of `${heading} ${text}`.toLocaleLowerCase().match(/[\p{L}][\p{L}\p{N}-]{2,}/gu) || []) {
    if (!STOP_WORDS.has(word)) frequency.set(word, (frequency.get(word) || 0) + 1);
  }
  for (const [word] of [...frequency.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))) {
    if (!candidates.some(item => item.toLocaleLowerCase() === word)) candidates.push(titleCase(word));
    if (candidates.length >= 3) break;
  }
  const concepts = candidates.slice(0, 3);
  const primaryConcept = concepts[0] || 'Teaching concept';
  return {
    topic: heading || primaryConcept,
    concepts,
    learningObjectives: [`Explain ${primaryConcept} using the supplied teaching material.`],
    sourceId: clean(sourceId) || null
  };
}

module.exports = { extractConcepts };
