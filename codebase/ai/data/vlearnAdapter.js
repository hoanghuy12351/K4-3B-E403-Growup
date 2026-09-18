'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { StringDecoder } = require('node:string_decoder');
const { findRepositoryRoot, DEFAULTS } = require('../config');

function listFiles(directory) {
  const files = [];
  const pending = [directory];
  while (pending.length) {
    const current = pending.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const item = path.join(current, entry.name);
      if (entry.isDirectory()) pending.push(item);
      else if (entry.isFile()) files.push(item);
    }
  }
  return files;
}

/** Discover the pack from filenames so the adapter does not depend on a fixed local layout. */
function discoverDatasetPaths(repositoryRoot) {
  const dataRoot = path.join(repositoryRoot, 'data');
  if (!fs.existsSync(dataRoot)) return { dataRoot };
  const files = listFiles(dataRoot);
  const chatlog = files.find(file => path.basename(file).toLocaleLowerCase() === 'tutor_turns.csv');
  const chatlogDirectory = chatlog && path.dirname(chatlog);
  const packRoot = chatlogDirectory && path.dirname(chatlogDirectory);
  const dictionary = chatlogDirectory && files.find(file => path.dirname(file) === chatlogDirectory && path.basename(file).toLocaleLowerCase() === 'data_dictionary.md');
  const transcript = packRoot && path.join(packRoot, 'transcript');
  const slides = packRoot && path.join(packRoot, 'slides');
  return { dataRoot, chatlog, dictionary, transcript, slides };
}

/** Parse RFC-style CSV records from a stream without loading the file into memory. */
async function* parseCsvRecords(filePath) {
  const stream = fs.createReadStream(filePath, { encoding: 'utf8' });
  const decoder = new StringDecoder('utf8');
  let field = '';
  let record = [];
  let quoted = false;
  let pendingQuote = false;

  const emit = () => {
    record.push(field);
    const finished = record;
    field = '';
    record = [];
    return finished;
  };

  for await (const chunk of stream) {
    const text = decoder.write(chunk);
    for (let index = 0; index < text.length; index += 1) {
      const char = text[index];
      if (pendingQuote) {
        if (char === '"') { field += '"'; pendingQuote = false; continue; }
        quoted = false;
        pendingQuote = false;
      }
      if (quoted) {
        if (char === '"') pendingQuote = true;
        else field += char;
        continue;
      }
      if (char === '"' && field.length === 0) { quoted = true; continue; }
      if (char === ',') { record.push(field); field = ''; continue; }
      if (char === '\n') { yield emit(); continue; }
      if (char !== '\r') field += char;
    }
  }
  const tail = decoder.end();
  if (tail) field += tail;
  if (pendingQuote) quoted = false;
  if (field.length || record.length) yield emit();
}

function normalizeText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function tokens(value) {
  return normalizeText(value).toLocaleLowerCase().match(/[\p{L}\p{N}]{2,}/gu) || [];
}

function normalizeRow(headers, values) {
  const row = Object.fromEntries(headers.map((header, index) => [header, values[index] || '']));
  return {
    turnId: row.turn_id,
    lectureCode: row.lecture_code,
    lectureTitle: row.lecture_title,
    studentQuestion: normalizeText(row.student_question),
    askedAt: row.asked_at_vn,
    cohortHint: row.cohort_hint
  };
}

function matchesFilters(item, { query, lectureCode, lectureTitle, cohortHint }) {
  if (lectureCode && item.lectureCode.toLocaleLowerCase() !== String(lectureCode).toLocaleLowerCase()) return false;
  if (lectureTitle && !item.lectureTitle.toLocaleLowerCase().includes(String(lectureTitle).toLocaleLowerCase())) return false;
  if (cohortHint && item.cohortHint.toLocaleLowerCase() !== String(cohortHint).toLocaleLowerCase()) return false;
  const queryTerms = tokens(query);
  if (!queryTerms.length) return true;
  const haystack = `${item.lectureTitle} ${item.studentQuestion}`.toLocaleLowerCase();
  return queryTerms.every(term => haystack.includes(term));
}

/** Create a bounded, read-only adapter for the local VLearn evidence pack. */
function createVlearnAdapter({ repositoryRoot = findRepositoryRoot(), scanLimit = DEFAULTS.searchScanLimit } = {}) {
  const paths = discoverDatasetPaths(repositoryRoot);

  function validateDataset() {
    const required = ['chatlog', 'dictionary', 'transcript', 'slides'];
    const missing = required.filter(key => !paths[key] || !fs.existsSync(paths[key])).map(key => `${key}: ${paths[key] || 'not discovered'}`);
    if (missing.length) throw new Error(`VLearn dataset is incomplete. Missing ${missing.join(', ')}.`);
  }

  async function getHeaders() {
    validateDataset();
    for await (const record of parseCsvRecords(paths.chatlog)) return record;
    throw new Error(`VLearn chatlog has no header row: ${paths.chatlog}`);
  }

  async function searchStudentQuestions(filters = {}) {
    validateDataset();
    const limit = Math.max(1, Math.min(Number(filters.limit) || DEFAULTS.historicalQuestionLimit, 100));
    const results = [];
    let headers;
    let scanned = 0;
    for await (const record of parseCsvRecords(paths.chatlog)) {
      if (!headers) { headers = record; continue; }
      scanned += 1;
      if (scanned > scanLimit || results.length >= limit) break;
      const item = normalizeRow(headers, record);
      if (matchesFilters(item, filters)) results.push(item);
    }
    return results;
  }

  async function getQuestionExamplesForConcept({ concepts = [], limit = DEFAULTS.historicalQuestionLimit } = {}) {
    const query = concepts.map(normalizeText).filter(Boolean).join(' ');
    if (!query) return [];
    const strictMatches = await searchStudentQuestions({ query, limit });
    if (strictMatches.length) return strictMatches;
    const results = [];
    for (const concept of concepts) {
      const remaining = Math.max(0, limit - results.length);
      if (!remaining) break;
      const matches = await searchStudentQuestions({ query: concept, limit: remaining });
      for (const match of matches) if (!results.some(item => item.turnId === match.turnId)) results.push(match);
    }
    return results.slice(0, limit);
  }

  function getDatasetInfo() {
    validateDataset();
    return {
      repositoryRoot,
      dataRoot: paths.dataRoot,
      chatlogPath: paths.chatlog,
      dataDictionaryPath: paths.dictionary,
      transcriptPaths: fs.readdirSync(paths.transcript).filter(name => /\.(md|txt)$/i.test(name)).map(name => path.join(paths.transcript, name)),
      slidePaths: fs.readdirSync(paths.slides).filter(name => /\.pdf$/i.test(name)).map(name => path.join(paths.slides, name))
    };
  }

  return { getDatasetInfo, searchStudentQuestions, getQuestionExamplesForConcept, getHeaders };
}

module.exports = { createVlearnAdapter, parseCsvRecords, discoverDatasetPaths };
