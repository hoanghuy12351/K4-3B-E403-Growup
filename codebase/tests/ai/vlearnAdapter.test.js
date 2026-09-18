'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { createVlearnAdapter } = require('../../ai');

test('VLearn adapter discovers the existing data pack and returns normalized bounded questions', async () => {
  const adapter = createVlearnAdapter();
  const info = adapter.getDatasetInfo();
  assert.match(info.chatlogPath, /data[\\/]vlearn-pack[\\/]chatlog[\\/]tutor_turns\.csv$/);
  assert.ok(info.transcriptPaths.length >= 1);
  assert.ok(info.slidePaths.length >= 1);
  const rows = await adapter.searchStudentQuestions({ lectureCode: 'D01', limit: 2 });
  assert.ok(rows.length > 0 && rows.length <= 2);
  assert.deepEqual(Object.keys(rows[0]), ['turnId', 'lectureCode', 'lectureTitle', 'studentQuestion', 'askedAt', 'cohortHint']);
});
