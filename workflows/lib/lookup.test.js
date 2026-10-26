// CF-019 — tests of the lookup tools on the real tables. Run: node --test workflows/lib/lookup.test.js
// Exam cases replay the 12 verified T2 rows; contact / request cases come from verified T3 rows and the tables.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const L = require('./lookup.js');

const ROOT = path.resolve(__dirname, '../..');
const csv = f => L.parseCsv(fs.readFileSync(path.join(ROOT, f), 'utf8'));
const CAL = csv('data/tables/exam_calendar.csv');
const DIR = csv('data/tables/directory.csv');
const REQ = csv('data/tables/request_catalogue.csv');
const T2 = csv('eval/testsets/T2_calendar.csv');

test('tables parse with the expected sizes', () => {
  assert.equal(CAL.length, 1560);
  assert.equal(DIR.length, 18);
  assert.equal(REQ.length, 24);
});

// ---------------------------------------------------------------- exam (T2 replay + edge cases)
for (const t of T2) {
  test(`exam ${t.id}: ${t.class_group} · ${t.module} · ${t.session}`, () => {
    const r = L.lookupExam(CAL, { module: t.module, class_group: t.class_group, session: t.session });
    if (t.expected_date === 'not found') return assert.equal(r.status, 'not_found');
    if (t.expected_date.startsWith('non communiqué (pas encore')) return assert.equal(r.status, 'not_published');
    assert.equal(r.status, 'found');
    assert.equal(r.count, 1);
    const m = r.matches[0];
    const nc = v => (v === 'non communiqué' ? null : v);
    assert.deepEqual([m.date, m.start_time, m.end_time, m.room],
      [t.expected_date, t.expected_start_time, nc(t.expected_end_time), nc(t.expected_room)]);
  });
}

test('exam: case, accents and code are normalised', () => {
  const a = L.lookupExam(CAL, { module: 'advanced deep learning', class_group: '5ds6', session: 'session principale' });
  const b = L.lookupExam(CAL, { module: 'DS14', class_group: '5DS6', session: 'Principale' });
  assert.equal(a.matches[0].exam_id, 'FX001');
  assert.equal(b.matches[0].exam_id, 'FX001');
});

test('exam: « session de contrôle » means Rattrapage', () => {
  const r = L.lookupExam(CAL, { module: 'DS14', class_group: '5DS6', session: 'session de contrôle' });
  assert.equal(r.matches[0].session, 'Rattrapage');
});

test('exam: missing class or module → needs_input, never a guess', () => {
  assert.deepEqual(L.lookupExam(CAL, { module: 'DS14' }).needs, ['class_group']);
  assert.deepEqual(L.lookupExam(CAL, { class_group: '5DS6' }).needs, ['module']);
});

test('exam: no session → both sessions returned', () => {
  const r = L.lookupExam(CAL, { module: 'DS14', class_group: '5DS6' });
  assert.deepEqual(r.matches.map(m => m.session).sort(), ['Principale', 'Rattrapage']);
});

test('exam: projected rows keep room and end time null', () => {
  const r = L.lookupExam(CAL, { module: 'Financial Analysis', class_group: '3A1', session: 'Principale' });
  assert.equal(r.matches[0].room, null);
  assert.equal(r.matches[0].end_time, null);
  assert.match(r.matches[0].data_status, /projected/);
});

// ---------------------------------------------------------------- contact
test('contact: by role id (FIN)', () => {
  const r = L.lookupContact(DIR, { role_id: 'fin' });
  assert.equal(r.contact.email, 'finance@esprit.tn');
});

test('contact: class 4SE1 → service élèves 4e année (T3-01)', () => {
  assert.equal(L.lookupContact(DIR, { class_group: '4SE1' }).contact.role_id, 'SCO-4A');
});

test('contact: escalation from SCO-3A follows reports_to (T3-09)', () => {
  const r = L.lookupContact(DIR, { role_id: 'SCO-3A' });
  assert.deepEqual(r.escalation_path.slice(0, 2), ['DEP-HEAD', 'DIR-ETU']);
});

test('contact: topic « mobilité internationale » → MOB', () => {
  assert.equal(L.lookupContact(DIR, { topic: 'mobilité internationale' }).contact.role_id, 'MOB');
});

test('contact: unknown role → not_found; empty query → needs_input', () => {
  assert.equal(L.lookupContact(DIR, { role_id: 'XYZ' }).status, 'not_found');
  assert.equal(L.lookupContact(DIR, {}).status, 'needs_input');
});

// ---------------------------------------------------------------- request
test('request: REQ-01 attestation for 4SE1 → SCO-4A (SCO-LEVEL resolved, T3-01)', () => {
  const r = L.lookupRequest(REQ, DIR, { request_id: 'REQ-01', class_group: '4SE1' });
  assert.equal(r.handler_role_id, 'SCO-4A');
  assert.equal(r.contact.email.length > 0, true);
});

test('request: REQ-08 without regime → needs the regime, both variants listed', () => {
  const r = L.lookupRequest(REQ, DIR, { request_id: 'REQ-08' });
  assert.equal(r.status, 'needs_input');
  assert.deepEqual(r.candidates.sort(), ['REQ-08-J', 'REQ-08-SA']);
});

test('request: REQ-08 regime soir → REQ-08-SA, 48 h rule (T3-03)', () => {
  const r = L.lookupRequest(REQ, DIR, { request_id: 'REQ-08', regime: 'soir' });
  assert.equal(r.request.request_id, 'REQ-08-SA');
  assert.match(r.request.deadline_rule, /48 h/);
});

test('request: REQ-17 → MOB, REQ-19 → FIN, FICTITIOUS flagged (T3-07, T3-08)', () => {
  const a = L.lookupRequest(REQ, DIR, { request_id: 'REQ-17' });
  const b = L.lookupRequest(REQ, DIR, { request_id: 'REQ-19' });
  assert.equal(a.handler_role_id, 'MOB');
  assert.equal(b.handler_role_id, 'FIN');
  assert.equal(b.is_fictitious, true);
});

test('request: topic « convention de stage » → REQ-14 (STAGE, T3-06)', () => {
  const r = L.lookupRequest(REQ, DIR, { topic: 'convention de stage', regime: 'jour' });
  assert.equal(r.request.request_id, 'REQ-14');
  assert.equal(r.handler_role_id, 'STAGE');
});

test('request: REQ-14 is for cours du jour only → not_applicable for soir', () => {
  assert.equal(L.lookupRequest(REQ, DIR, { request_id: 'REQ-14', regime: 'soir' }).status, 'not_applicable');
});

test('request: unknown id → not_found', () => {
  assert.equal(L.lookupRequest(REQ, DIR, { request_id: 'REQ-99' }).status, 'not_found');
});
