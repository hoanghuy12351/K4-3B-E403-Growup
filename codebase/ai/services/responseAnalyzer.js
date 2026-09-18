'use strict';

const { DEFAULTS } = require('../config');

/** Aggregate one-tap responses using configurable, non-validated heuristic thresholds. */
function analyzeResponses({ question, responses = [], thresholds = DEFAULTS.responseThresholds } = {}) {
  if (!question?.options?.length) throw new Error('Response analysis requires a diagnostic question with options.');
  const options = new Map(question.options.map(option => [option.id, option]));
  const accepted = responses.filter(response => options.has(response.optionId));
  const correctCount = accepted.filter(response => options.get(response.optionId).correct).length;
  const totalResponses = accepted.length;
  const correctRate = totalResponses ? Number((correctCount / totalResponses).toFixed(3)) : 0;
  const status = correctRate >= thresholds.understood ? 'understood' : correctRate >= thresholds.uncertain ? 'uncertain' : 'needs_attention';
  const signalCounts = new Map();
  for (const response of accepted) {
    const misconceptionId = options.get(response.optionId).misconceptionId;
    if (misconceptionId) signalCounts.set(misconceptionId, (signalCounts.get(misconceptionId) || 0) + 1);
  }
  const misconceptionSignals = [...signalCounts.entries()].map(([misconceptionId, count]) => ({ misconceptionId, count, ratio: Number((count / totalResponses).toFixed(3)) }));
  const recommendation = status === 'understood' ? 'Continue to the next concept block.' : status === 'uncertain' ? 'Ask for one brief clarification before continuing.' : `Briefly clarify ${question.concept} before continuing.`;
  return { totalResponses, correctRate, status, misconceptionSignals, recommendation };
}

module.exports = { analyzeResponses };
