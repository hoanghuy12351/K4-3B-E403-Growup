'use strict';

const fs = require('node:fs');
const path = require('node:path');

const DEFAULTS = Object.freeze({
  historicalQuestionLimit: 30,
  questionCount: 1,
  searchScanLimit: 15000,
  responseThresholds: Object.freeze({ understood: 0.8, uncertain: 0.6 })
});

/** Find the repository root without relying on a machine-specific path. */
function findRepositoryRoot(startDirectory = __dirname) {
  let current = path.resolve(startDirectory);
  while (true) {
    if (fs.existsSync(path.join(current, 'data')) && fs.existsSync(path.join(current, 'codebase'))) return current;
    const parent = path.dirname(current);
    if (parent === current) throw new Error('Could not locate repository root containing data/ and codebase/.');
    current = parent;
  }
}

module.exports = { DEFAULTS, findRepositoryRoot };
