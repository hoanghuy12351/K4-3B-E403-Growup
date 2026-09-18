'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { analyzeResponses } = require('../../ai');

test('response analyzer maps wrong answer selections to misconception signals', () => {
  const result = analyzeResponses({ question: { concept: 'retrieval', options: [{ id: 'A', correct: false, misconceptionId: 'M001' }, { id: 'B', correct: true, misconceptionId: null }] }, responses: [{ optionId: 'A' }, { optionId: 'A' }, { optionId: 'B' }] });
  assert.equal(result.totalResponses, 3);
  assert.equal(result.correctRate, 0.333);
  assert.equal(result.status, 'needs_attention');
  assert.deepEqual(result.misconceptionSignals, [{ misconceptionId: 'M001', count: 2, ratio: 0.667 }]);
});
