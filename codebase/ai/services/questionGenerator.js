'use strict';

function clean(value) { return String(value || '').replace(/\s+/g, ' ').trim(); }
function firstRelevantSentence(text, concept) {
  const sentences = clean(text).match(/[^.!?]+[.!?]?/g) || [];
  return clean(sentences.find(sentence => sentence.toLocaleLowerCase().includes(concept.toLocaleLowerCase())) || sentences[0] || 'The supplied teaching material defines this concept.');
}

/** Create one reviewable, source-grounded multiple-choice diagnostic question without an external model. */
function generateDiagnosticQuestion({ conceptContext = {}, misconceptions = [], sourceContext = {} } = {}) {
  const concept = clean(conceptContext.concepts?.[0]) || clean(conceptContext.topic);
  const sourceText = clean(sourceContext.text || sourceContext.sourceText);
  if (!concept || !sourceText) throw new Error('Question generation requires a concept and supplied teaching material.');
  const relevantMisconceptions = misconceptions.filter(item => clean(item.concept).toLocaleLowerCase() === concept.toLocaleLowerCase());
  const correctText = firstRelevantSentence(sourceText, concept);
  const options = [{ id: 'A', text: correctText, correct: true, misconceptionId: null }];
  for (const item of relevantMisconceptions.slice(0, 3)) options.push({ id: String.fromCharCode(65 + options.length), text: item.statement, correct: false, misconceptionId: item.id });
  if (options.length === 1) options.push({ id: 'B', text: `${concept} is unrelated to the supplied teaching material.`, correct: false, misconceptionId: null });
  return {
    id: `Q-${clean(sourceContext.sourceId || conceptContext.sourceId || concept).replace(/[^\w]+/g, '-').replace(/^-|-$/g, '').toUpperCase() || '001'}`,
    topic: clean(conceptContext.topic) || concept,
    concept,
    question: `Which statement about ${concept} is supported by the supplied teaching material?`,
    learningObjective: clean(conceptContext.learningObjectives?.[0]) || `Explain ${concept} using the supplied teaching material.`,
    source: [{ type: 'slide', id: clean(sourceContext.sourceId || conceptContext.sourceId) || 'teacher-supplied-context' }],
    options
  };
}

module.exports = { generateDiagnosticQuestion };
