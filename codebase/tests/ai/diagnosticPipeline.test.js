'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { extractConcepts, mineMisconceptions, generateDiagnosticCheck, validateDiagnosticQuestion } = require('../../ai');

test('deterministic services preserve evidence IDs and generate a schema-valid question', async () => {
  const context = extractConcepts({ title: 'Tokenization', sourceText: 'A token can be a word, part of a word, or a character.', sourceId: 'slide-12' });
  assert.equal(context.topic, 'Tokenization');
  assert.ok(context.concepts.length > 0);
  const mined = mineMisconceptions({ concepts: ['token'], historicalQuestions: [{ turnId: 'T00001', studentQuestion: 'What is the difference between a token and a word?' }] });
  assert.equal(mined.misconceptions[0].evidence[0].turnId, 'T00001');
  const result = await generateDiagnosticCheck({ teachingContext: { title: 'Tokenization', text: 'A token can be a word, part of a word, or a character.', sourceId: 'slide-12' }, options: { historicalQuestionLimit: 2 } });
  assert.equal(result.questions.length, 1);
  assert.equal(validateDiagnosticQuestion(result.questions[0]).valid, true);
});
