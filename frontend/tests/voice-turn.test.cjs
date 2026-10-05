const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const path = require('node:path');
const code = ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src/utils/voiceTurn.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
}).outputText;
const context = { exports: {} }; vm.runInNewContext(code, context);
const { stripAssistantEcho } = context.exports;
test('ignore an exact English or Hindi AI question', () => {
  assert.equal(stripAssistantEcho('Which district do you live in?', 'Which district do you live in?'), '');
  assert.equal(stripAssistantEcho('आप किस जिले में रहते हैं?', 'आप किस जिले में रहते हैं?'), '');
});
test('preserve short and conversational answers', () => {
  assert.equal(stripAssistantEcho('Moradabad', 'Which district do you live in?'), 'Moradabad');
  assert.equal(stripAssistantEcho('I live in Moradabad with my family.', 'Which district do you live in?'), 'I live in Moradabad with my family.');
  assert.equal(stripAssistantEcho('I would like to learn sewing.', 'What kind of work would you like to learn?'), 'I would like to learn sewing.');
});
test('remove the question when it precedes or follows the real answer', () => {
  const question = 'Which district do you live in?';
  assert.equal(stripAssistantEcho(`${question} Moradabad.`, question), 'Moradabad');
  assert.equal(stripAssistantEcho(`Moradabad. ${question}`, question), 'Moradabad');
  assert.equal(stripAssistantEcho('आप किस जिले में रहते हैं? मैं मुरादाबाद में रहता हूँ।', 'आप किस जिले में रहते हैं?'), 'मैं मुरादाबाद में रहता हूँ');
});
