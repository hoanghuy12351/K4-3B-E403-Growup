'use strict';

const { DEFAULTS } = require('./config');
const { createVlearnAdapter } = require('./data/vlearnAdapter');
const { extractConcepts } = require('./services/conceptExtractor');
const { mineMisconceptions } = require('./services/misconceptionMiner');
const { generateDiagnosticQuestion } = require('./services/questionGenerator');
const { analyzeResponses } = require('./services/responseAnalyzer');

function validateDiagnosticQuestion(question) {
  const required = ['id', 'topic', 'concept', 'question', 'learningObjective', 'source', 'options'];
  const missing = required.filter(key => !question?.[key] || (Array.isArray(question[key]) && !question[key].length));
  if (missing.length) return { valid: false, errors: [`Missing required fields: ${missing.join(', ')}`] };
  const correct = question.options.filter(option => option.correct === true);
  const invalidOption = question.options.find(option => !option.id || !option.text || typeof option.correct !== 'boolean' || !Object.hasOwn(option, 'misconceptionId'));
  if (invalidOption) return { valid: false, errors: ['Every option must have id, text, correct, and misconceptionId.'] };
  if (correct.length !== 1) return { valid: false, errors: ['Exactly one option must be marked correct.'] };
  if (correct[0].misconceptionId !== null) return { valid: false, errors: ['A correct option must have misconceptionId: null.'] };
  return { valid: true, errors: [] };
}

/** Run the Phase 1 deterministic pipeline before a lecturer triggers a classroom micro-check. */
async function generateDiagnosticCheck({ teachingContext = {}, options = {}, adapter = createVlearnAdapter() } = {}) {
  const context = extractConcepts({ sourceText: teachingContext.text, title: teachingContext.title, sourceId: teachingContext.sourceId });
  const historicalQuestions = await adapter.getQuestionExamplesForConcept({ concepts: context.concepts, limit: options.historicalQuestionLimit || DEFAULTS.historicalQuestionLimit });
  const mined = mineMisconceptions({ concepts: context.concepts, historicalQuestions });
  const questionCount = Math.max(1, Math.min(Number(options.questionCount) || DEFAULTS.questionCount, 1));
  const questions = Array.from({ length: questionCount }, () => generateDiagnosticQuestion({ conceptContext: context, misconceptions: mined.misconceptions, sourceContext: teachingContext }));
  for (const question of questions) {
    const validation = validateDiagnosticQuestion(question);
    if (!validation.valid) throw new Error(`Generated diagnostic question is invalid: ${validation.errors.join(' ')}`);
  }
  return { context, historicalEvidence: { matchedQuestions: historicalQuestions.length }, misconceptions: mined.misconceptions, questions };
}

module.exports = { createVlearnAdapter, extractConcepts, mineMisconceptions, generateDiagnosticQuestion, analyzeResponses, validateDiagnosticQuestion, generateDiagnosticCheck };
