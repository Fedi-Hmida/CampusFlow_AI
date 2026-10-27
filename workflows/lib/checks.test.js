// CF-010 — tests of the deterministic Critic checks (ADR-010). Run: node --test workflows/lib/checks.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const { checkReply } = require('./checks.js');

const RETRIEVED = [
  { article_keys: ['D1-001/7-8/Déroulement des épreuves'], doc_status: 'official',
    text: "Les certificats médicaux ne constituent pas un justificatif d'absence. Le 15/01/2027 à 09h00 en salle B12." },
  { article_keys: ['D1-004/2/Absence à un examen final ou à un DS'], doc_status: 'FICTITIOUS',
    text: '[DOCUMENT FICTIF] Déposer le dossier dans un délai de 48 h auprès de scolarite@esprit.tn.' },
];
const ok = r => checkReply(r, { retrieved: RETRIEVED });
const fails = r => ok(r).failures.map(f => f.check);

test('grounded, cited reply passes', () => {
  const r = ok("En cours du jour, un certificat médical ne justifie pas l'absence [D1-001, art. 7-8, p. 9].");
  assert.equal(r.pass, true, JSON.stringify(r.failures));
});

test('a rule without any citation fails', () => {
  assert.deepEqual(fails("Un certificat médical ne justifie pas l'absence."), ['citation_present']);
});

test('citing an article that was not retrieved fails', () => {
  assert.ok(fails("Voir le règlement [D1-002, art. 9, p. 4].").includes('citation_retrieved'));
});

test('a date, time or room absent from the evidence fails', () => {
  assert.ok(fails("L'épreuve est le 16/01/2027 à 10h00 en salle C21 [D1-001, art. 7-8, p. 9].").includes('facts_grounded'));
  assert.equal(ok("L'épreuve est le 15/01/2027 à 09h00 en salle B12 [D1-001, art. 7-8, p. 9].").pass, true);
});

test('a delay or e-mail absent from the evidence fails', () => {
  assert.ok(fails("Prévenir dans les 72 h : examens@esprit.tn [D1-004, art. 2]. (procédure de démonstration)").includes('facts_grounded'));
});

test('using a FICTITIOUS source without saying so fails', () => {
  assert.ok(fails('Déposer le dossier sous 48 h à scolarite@esprit.tn [D1-004, art. 2].').includes('fictif_labelled'));
  assert.equal(ok('Procédure de démonstration (fictive) : déposer le dossier sous 48 h à scolarite@esprit.tn [D1-004, art. 2].').pass, true);
});

test('claiming the bot sent something fails', () => {
  assert.ok(fails("J'ai envoyé ta demande à la scolarité [D1-001, art. 7-8, p. 9].").includes('not_sent'));
});

test('« not found » needs a contact', () => {
  assert.deepEqual(fails('Information non trouvée dans le règlement.'), ['not_found_contact']);
  assert.equal(ok('Information non trouvée dans le règlement. Contacte scolarite@esprit.tn.').pass, true);
});

test('page numbers and article numbers are not treated as facts to ground', () => {
  assert.equal(ok("Voir l'article 7-8 [D1-001, art. 7-8, p. 9] : pas de certificat médical comme justificatif.").pass, true);
});

test('a directory contact passed as allowed is not an invented fact', () => {
  const reply = 'Information non trouvée dans le règlement. Contacte le service financier (finance@esprit.tn).';
  assert.deepEqual(fails(reply), ['facts_grounded']);
  assert.equal(checkReply(reply, { retrieved: RETRIEVED, allowed: ['finance@esprit.tn'] }).pass, true);
});

test('empty reply fails', () => {
  assert.equal(ok('').pass, false);
});

// CF-404 — the « Checks again » node embeds checks.js and assistant.js in one scope (as build_wf3.py does).
// assistant.js has its own citations(); checkReply must not pick it up (live 27 Oct: a valid revision was rejected).
test('checkReply still works when embedded together with assistant.js', () => {
  const fs = require('node:fs');
  const path = require('node:path');
  const src = f => fs.readFileSync(path.join(__dirname, f), 'utf8');
  const embedded = new Function(`${src('checks.js')}\n${src('assistant.js')}\nreturn checkReply;`)();
  const reply = "Les certificats médicaux ne sont pas un justificatif [D1-001, art. 7-8, p. 9].";
  assert.deepEqual(embedded(reply, { retrieved: RETRIEVED }).failures, []);
});

// CF-807 — Regulations v3 review (D5-007): an OFFICIAL regulation was labelled « procédure de démonstration »
test('an official source labelled as a demonstration procedure fails; a FICTITIOUS one labelled passes', () => {
  assert.ok(fails('Note retenue : la meilleure moyenne [D1-001, art. 7-8, p. 9] (procédure de démonstration).').includes('official_labelled_fictif'));
  assert.ok(fails('Note retenue : la meilleure moyenne [D1-001, art. 7-8, p. 9 (procédure de démonstration)].').includes('official_labelled_fictif'));
  assert.equal(ok('Dossier sous 48 h à scolarite@esprit.tn [D1-004, art. 2] (procédure de démonstration).').pass, true);
});
