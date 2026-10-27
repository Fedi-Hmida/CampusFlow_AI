// ESA-401 — tests of the WF-3 pure logic (workflows/lib/assistant.js). Run: node --test workflows/lib/assistant.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const A = require('./assistant.js');

test('normalizeInput: test webhook body → canonical input', () => {
  const x = A.normalizeInput({ body: { test_id: 'T1-07', question: '  Quand ?  ', regime: 'jour', class_group: '5DS6', mode: 'local' } }, 'hybrid');
  assert.deepEqual(x, { source: 'test', test_id: 'T1-07', question: 'Quand ?', regime: 'jour', class_group: '5DS6', photo: null, mode: 'local', chat: null });
});

test('normalizeInput: Telegram update → canonical input; invalid mode falls back to config', () => {
  const x = A.normalizeInput({ message: { chat: { id: 42 }, text: 'Bonjour' } }, 'hybrid');
  assert.equal(x.source, 'telegram'); assert.equal(x.chat, 42); assert.equal(x.question, 'Bonjour'); assert.equal(x.mode, 'hybrid');
  assert.equal(A.normalizeInput({ body: { question: 'x', mode: 'cloud' } }, 'hybrid').mode, 'hybrid');
});

test('regimeFromText: stated regime only, never inferred from the class', () => {
  assert.equal(A.regimeFromText('Je suis en cours du soir'), 'soir');
  assert.equal(A.regimeFromText('alternance : absence'), 'alternance');
  assert.equal(A.regimeFromText('Je suis en 5DS6'), null);
});

test('parseRouter: valid JSON → route; broken JSON → safe regulations route', () => {
  const r = A.parseRouter('{"language":"fr","intents":["calendar"],"entities":{"module":"DS14","class_group":"5DS6"},"missing_fields":[]}');
  assert.deepEqual(r.intents, ['calendar']); assert.equal(r.entities.module, 'DS14');
  const bad = A.parseRouter('not json');
  assert.deepEqual(bad.intents, ['regulations']); assert.equal(bad.parse_error, true);
});

test('decidePaths: out of scope wins alone; known intents kept in a fixed order; photo adds vision', () => {
  assert.deepEqual(A.decidePaths({ intents: ['out_of_scope'] }, false), ['out_of_scope']);
  assert.deepEqual(A.decidePaths({ intents: ['admin', 'regulations'] }, false), ['regulations', 'admin']);
  assert.deepEqual(A.decidePaths({ intents: ['calendar'] }, true), ['vision', 'calendar']);
  assert.deepEqual(A.decidePaths({ intents: ['out_of_scope', 'calendar'] }, false), ['calendar']);
});

test('ref: reference header from a chunk payload', () => {
  assert.equal(A.ref({ doc_id: 'D1-001', article_keys: ['D1-001/7-8/Déroulement des épreuves'], page_start: 9 }), '[D1-001, art. 7-8, p. 9]');
});

test('regulationsUser: regime wording, question, numbered excerpts with references and status', () => {
  const u = A.regulationsUser('Quelle règle ?', null, [{ doc_id: 'D1-004', article_keys: ['D1-004/2/Absence'], page_start: 1, doc_status: 'FICTITIOUS', text: 'texte' }]);
  assert.match(u, /Régime de l'étudiant : non précisé/);
  assert.match(u, /\[D1-004, art\. 2, p\. 1\] \(FICTIF\)\ntexte/);
});

test('citations: parsed from the reply text', () => {
  assert.deepEqual(A.citations('Règle [D1-001, art. 7-8, p. 9] et [D1-004, art. 2].'),
    [{ doc_id: 'D1-001', article: '7-8', page: 9 }, { doc_id: 'D1-004', article: '2', page: null }]);
});

test('calendarReply: found / projected (non communiqué) / needs input / not found', () => {
  const found = A.calendarReply({ found: true, status: 'found', matches: [{ module_name: 'Advanced Deep Learning', class_group: '5DS6', session: 'Principale', assessment: 'Examen', date: '2027-01-15', start_time: '09:00', end_time: '11:00', room: 'B12', data_status: 'FICTITIOUS', last_updated: '2026-10-25' }] }, 'fr');
  assert.match(found, /vendredi 15\/01\/2027/i); assert.match(found, /09:00.*11:00/); assert.match(found, /B12/); assert.match(found, /démonstration/);
  const proj = A.calendarReply({ found: true, status: 'found', matches: [{ module_name: 'Financial Analysis', class_group: '3A1', session: 'Principale', assessment: 'Examen', date: '2026-10-27', start_time: '09:00', end_time: null, room: null, data_status: 'projected from 2025-2026', last_updated: '2026-10-25' }] }, 'fr');
  assert.match(proj, /salle non communiquée/); assert.match(proj, /fin non communiquée/); assert.match(proj, /prévisionnel/);
  assert.match(A.calendarReply({ found: false, status: 'needs_input', needs: ['class_group'] }, 'fr'), /classe/);
  assert.match(A.calendarReply({ found: false, status: 'not_found' }, 'fr'), /examen@esprit\.tn/);
});

test('contactReply: office + e-mail + escalation; request with documents and delay', () => {
  const c = A.contactReply({ found: true, contact: { role_title: 'Service financier', email: 'finance@esprit.tn', office: 'Bloc B, bureau 03', hours: 'Lundi-vendredi' }, escalation_path: ['DIR'] }, null, 'fr');
  assert.match(c, /Service financier/); assert.match(c, /finance@esprit\.tn/);
  const r = A.contactReply({ found: true, status: 'found', request: { request_type: "Attestation", required_documents: 'Carte étudiant ; Demande', deadline_rule: 'Aucun délai', processing_time: '2 jours', source: 'FICTITIOUS — x' }, contact: { role_title: 'Service élèves 4e', email: 'service.eleves4eme@esprit.tn', office: 'Bloc G' }, is_fictitious: true }, null, 'fr');
  assert.match(r, /Carte étudiant/); assert.match(r, /démonstration/); assert.match(r, /service\.eleves4eme@esprit\.tn/);
  assert.match(A.contactReply({ found: false, status: 'needs_input', needs: ['regime'] }, null, 'fr'), /régime/);
});

test('refusal and fallback replies always give a contact', () => {
  assert.match(A.refusalReply('fr', false), /hors de mon périmètre/);
  assert.match(A.refusalReply('fr', true), /consignes/);
  assert.match(A.fallbackReply('fr'), /scolarite@esprit\.tn/);
  assert.match(A.refusalReply('en', false), /outside/);
});

test('mergeSections: one section per path, sources kept, no duplicate blank lines', () => {
  const m = A.mergeSections([{ title: 'Règle', text: 'A [D1-001, art. 9, p. 13]' }, { title: 'Démarche', text: 'B' }]);
  assert.equal(m, '📘 Règle\nA [D1-001, art. 9, p. 13]\n\n🗂️ Démarche\nB');
  assert.equal(A.mergeSections([{ title: 'Règle', text: 'seul' }]), 'seul');
});

test('contractResponse: shape required by eval/e2e/wf3_response.schema.json', () => {
  const r = A.contractResponse({ test_id: 'T1-01', reply: 'x', route: { intents: ['regulations'], entities: {}, missing_fields: [] }, paths: ['regulations'],
    citations: [], retrieved: [{ article_keys: ['D1-001/9/Assiduité'], doc_status: 'official', text: 'long' }], tool_rows: [],
    checks: { pass: true, failures: [] }, revised: false, fallback: false, timings: { total: 1.234 }, mode: 'hybrid', config: 'v' });
  assert.deepEqual(Object.keys(r).sort(), ['checks', 'citations', 'config', 'fallback', 'mode', 'reply', 'retrieved', 'revised', 'route', 'test_id', 'timings_s', 'tool_rows'].sort());
  assert.deepEqual(r.retrieved, [{ article_keys: ['D1-001/9/Assiduité'], doc_status: 'official' }]);
  assert.deepEqual(r.route.agents, ['regulations']); assert.deepEqual(r.checks, { pass: true, failures: [] });
  assert.equal(r.timings_s.total, 1.23);
});

test('regimeNote: asked only when the regime is unknown and the reply is a real rule', () => {
  assert.match(A.regimeNote(null, false, 'fr'), /cours du jour, du soir ou en alternance/);
  assert.equal(A.regimeNote('jour', false, 'fr'), '');
  assert.equal(A.regimeNote(null, true, 'fr'), '');
});

test('photoFacts: what the photo says, labelled as read on the photo; nothing when empty', () => {
  const t = A.photoFacts({ module_name: 'Probabilités', module_code: 'MATH201', class_group: '2A7', session: 'Rattrapage', date: '2027-06-16', start_time: '14:00', end_time: '16:00', room: 'C21' });
  assert.match(t, /lu sur ta photo/); assert.match(t, /mercredi 16\/06\/2027/); assert.match(t, /14:00 – 16:00/); assert.match(t, /salle C21/);
  assert.equal(A.photoFacts({ document_type: 'unrelated' }), '');
  assert.equal(A.photoFacts(null), '');
});

test('hashChat: stable, not reversible to the chat id', () => {
  assert.equal(A.hashChat(42), A.hashChat(42)); assert.notEqual(A.hashChat(42), '42'); assert.notEqual(A.hashChat(42), A.hashChat(43));
});

// CF-405 — a photo sent without a caption (live 27 Oct: refused as out of scope, Vision never ran)
test('decidePaths: a bare photo goes to Vision; a real out-of-scope question with a photo is still refused', () => {
  assert.deepEqual(A.decidePaths({ intents: ['out_of_scope'] }, true, ''), ['vision']);
  assert.deepEqual(A.decidePaths({ intents: ['out_of_scope'] }, true, 'Quelle est ma note ?'), ['out_of_scope']);
  assert.deepEqual(A.decidePaths({ intents: ['out_of_scope'], injection_suspected: true }, true, ''), ['out_of_scope']);
  assert.deepEqual(A.decidePaths({ intents: ['out_of_scope'] }, false, ''), ['out_of_scope']);
});

test('photoOnlyReply: what was read (labelled) + what do you want to know; unrelated and unreadable handled', () => {
  const t = A.photoOnlyReply({ document_type: 'convocation', module_name: 'Probabilités', module_code: 'MATH201', class_group: '2A7', session: 'Rattrapage', date: '2027-06-16', start_time: '14:00', end_time: '16:00', room: 'C21' }, 'fr');
  assert.match(t, /lu sur ta photo/); assert.match(t, /16\/06\/2027/); assert.match(t, /Que veux-tu savoir/);
  assert.match(A.photoOnlyReply({ document_type: 'unrelated' }, 'fr'), /ne ressemble pas/);
  assert.match(A.photoOnlyReply({ image_readable: false }, 'fr'), /n'arrive pas à lire/);
});

// CF-406 — Telegram UX found live on 27 Oct: « Bonjour » refused, citations' brackets eaten by Markdown,
// remembered regime applied silently.
test('smallTalk: greetings and commands are recognised; a greeting followed by a question is not', () => {
  for (const t of ['/start', 'Bonjour', 'Salut !', 'bonsoir', 'Hello', '/aide', '/help', '/foo']) assert.equal(A.smallTalk(t), 'start', t);
  for (const t of ['Merci', 'merci beaucoup !', 'Thanks']) assert.equal(A.smallTalk(t), 'thanks', t);
  assert.equal(A.smallTalk('/reset'), 'reset');
  for (const t of ["Bonjour, c'est quand l'examen de DS14 ?", 'Je suis en cours du soir', '', null]) assert.equal(A.smallTalk(t), null, String(t));
});

test('smallTalkReply: welcome with examples and /reset; reset and thanks answers', () => {
  const w = A.smallTalkReply('start', 'fr');
  assert.match(w, /Exemples/); assert.match(w, /\/reset/); assert.match(w, /régime/);
  assert.match(A.smallTalkReply('reset', 'fr'), /zéro/);
  assert.match(A.smallTalkReply('thanks', 'fr'), /plaisir/);
});

test('refusalReply: personal-data wording only for personal questions', () => {
  assert.match(A.refusalReply('fr', false, true), /dossiers personnels/);
  const g = A.refusalReply('fr', false, false);
  assert.match(g, /hors de mon périmètre/); assert.doesNotMatch(g, /dossiers personnels/);
  assert.equal(A.isPersonal('Quelle est ma note en Probabilités ?'), true);
  assert.equal(A.isPersonal('Quel temps fera-t-il demain ?'), false);
});

test('toTelegramHtml: text shown exactly as written (brackets kept, HTML escaped)', () => {
  assert.equal(A.toTelegramHtml('a < b & c > d [D1-001, art. 7-8, p. 9] *x_y*'), 'a &lt; b &amp; c &gt; d [D1-001, art. 7-8, p. 9] *x_y*');
});

test('regimeRecall: says which remembered regime was used', () => {
  const t = A.regimeRecall('soir', 'fr');
  assert.match(t, /cours du soir/); assert.match(t, /\/reset/);
  assert.equal(A.regimeRecall(null, 'fr'), '');
});

// CF-807 — the model's citation format, repaired in code (a 4B/Flash-Lite prompt rule was ignored on 2–3 of 32 dev replies)
test('normalizeCitations: one reference per bracket; the demo label follows exactly the FICTITIOUS references', () => {
  const F = new Set(['D1-004']);
  assert.equal(A.normalizeCitations('Règle [D1-002, art. 7-7, p. 7, D1-004, art. 7, p. 2 (procédure de démonstration)].', F, 'fr'),
    'Règle [D1-002, art. 7-7, p. 7] [D1-004, art. 7, p. 2] (procédure de démonstration).');
  assert.equal(A.normalizeCitations('Validée [D1-001, art. 7-4, p. 7; D1-002, art. 7-4, p. 6].', F, 'fr'),
    'Validée [D1-001, art. 7-4, p. 7] [D1-002, art. 7-4, p. 6].');
  assert.equal(A.normalizeCitations('Commission [D1-003, art. 8, p. 7] (procédure de démonstration) [D1-004, art. 5, p. 1].', F, 'fr'),
    'Commission [D1-003, art. 8, p. 7] [D1-004, art. 5, p. 1] (procédure de démonstration).');
  assert.equal(A.normalizeCitations('Motifs [D1-004, art. 5, p. 1].', F, 'fr'), 'Motifs [D1-004, art. 5, p. 1] (procédure de démonstration).');
  assert.equal(A.normalizeCitations('Rule [D1-004, art. 5, p. 1].', F, 'en'), 'Rule [D1-004, art. 5, p. 1] (demonstration procedure).');
  const plain = 'Zéro [D1-001, art. 7-8, p. 9]. Information non trouvée dans le règlement.';
  assert.equal(A.normalizeCitations(plain, F, 'fr'), plain);
});
