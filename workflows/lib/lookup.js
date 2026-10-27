// CF-019 — exact lookups on data/tables (exam calendar, directory, request catalogue).
// Pure functions: rows in, result out. Unit-tested by workflows/lib/lookup.test.js (node --test) and embedded verbatim
// into the n8n tool workflows by scripts/workflows/build_tools.py — the tested code is the deployed code.
// Rules: exact rows or { found: false }; never a partial guess; an empty cell stays null (shown « non communiqué »).

function norm(s) {
  return String(s ?? '').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ').trim();
}

function blankToNull(row) {
  const out = {};
  for (const [k, v] of Object.entries(row)) out[k] = v === '' || v === undefined ? null : v;
  return out;
}

function sessionOf(s) {
  const n = norm(s);
  if (!n) return null;
  if (/rattrapage|controle|session 2/.test(n)) return 'Rattrapage';
  if (/principale|session 1|normale/.test(n)) return 'Principale';
  return undefined;                                   // unknown wording → reported, never guessed
}

// Module query matches a row if it equals the code, or every word of the query is a word of the module name.
function moduleMatches(row, q) {
  const nq = norm(q);
  if (!nq) return false;
  if (norm(row.module_code) === nq) return true;
  const words = new Set(norm(row.module_name).split(' '));
  return nq.split(' ').every(w => words.has(w));
}

function lookupExam(rows, query) {
  const q = query || {};
  const needs = [];
  if (!norm(q.module)) needs.push('module');
  if (!norm(q.class_group)) needs.push('class_group');
  if (needs.length) return { found: false, status: 'needs_input', needs };
  const session = q.session ? sessionOf(q.session) : null;
  if (session === undefined) return { found: false, status: 'needs_input', needs: ['session'], note: `session « ${q.session} » not understood` };
  const cls = norm(q.class_group);
  let m = rows.filter(r => norm(r.class_group) === cls && moduleMatches(r, q.module));
  if (session) m = m.filter(r => r.session === session);
  if (!m.length) {
    const known = rows.some(r => norm(r.class_group) === cls && moduleMatches(r, q.module));
    return { found: false, status: known && session === 'Rattrapage' ? 'not_published' : 'not_found', matches: [] };
  }
  const modules = new Set(m.map(r => r.module_code));
  return { found: true, status: modules.size > 1 ? 'ambiguous' : 'found', count: m.length, matches: m.map(blankToNull) };
}

function escalation(dirRows, roleId) {
  const by = Object.fromEntries(dirRows.map(r => [r.role_id, r]));
  const path = [];
  let cur = by[roleId] && by[roleId].reports_to;
  while (cur && by[cur] && !path.includes(cur)) { path.push(cur); cur = by[cur].reports_to; }
  return path;
}

// Level service from a class group: 5DS6 → SCO-5A (first digit = year).
function levelRole(classGroup) {
  const m = String(classGroup || '').trim().match(/^([1-5])/);
  return m ? `SCO-${m[1]}A` : null;
}

function lookupContact(dirRows, query) {
  const q = query || {};
  let role = null;
  if (q.role_id) role = dirRows.find(r => r.role_id === String(q.role_id).trim().toUpperCase()) || null;
  else if (q.class_group && !q.topic) role = dirRows.find(r => r.role_id === levelRole(q.class_group)) || null;
  else if (norm(q.topic)) {
    const words = norm(q.topic).split(' ').filter(w => w.length > 2);
    const scored = dirRows.map(r => ({ r, s: words.filter(w => norm(`${r.role_title} ${r.handles}`).split(' ').includes(w)).length }))
      .filter(x => x.s > 0).sort((a, b) => b.s - a.s);
    if (scored.length > 1 && scored[0].s === scored[1].s) {
      return { found: false, status: 'ambiguous', candidates: scored.filter(x => x.s === scored[0].s).map(x => x.r.role_id) };
    }
    role = scored.length ? scored[0].r : null;
  } else return { found: false, status: 'needs_input', needs: ['role_id or topic or class_group'] };
  if (!role) return { found: false, status: 'not_found' };
  return { found: true, status: 'found', contact: blankToNull(role), escalation_path: escalation(dirRows, role.role_id) };
}

// Student wording → catalogue wording (found in the WF-3 smoke test: « double correction » never matched
// « Vérification de copie »). When a synonym matches, only its catalogue words are scored.
const SYNONYMS = [
  [/double correction|recorrection|revoir ma copie|contester (ma|une|mon) (note|copie)|reclamation (de|sur) (ma |une )?note/, 'verification copie'],
  [/(perdu|perte|oublie).{0,25}convocation|nouvelle convocation/, 'duplicata convocation'],
  [/plusieurs fois|echeancier|payer .{0,25}frais|paiement en (plusieurs|tranches)/, 'echeancier paiement'],
  [/certificat de scolarite/, 'attestation scolarite'],
  [/carte .{0,15}(perdue|volee)|(perdu|perte).{0,15}carte/, 'duplicata carte etudiant'],
  [/bulletin de notes|mes notes officielles/, 'releve notes'],
];

function topicWords(topic) {
  const n = norm(topic);
  const hit = SYNONYMS.find(([re]) => re.test(n));
  return (hit ? hit[1] : n).split(' ').filter(w => w.length > 2);
}

function lookupRequest(reqRows, dirRows, query) {
  const q = query || {};
  let cands;
  if (q.request_id) {
    const id = String(q.request_id).trim().toUpperCase();
    cands = reqRows.filter(r => r.request_id === id || r.request_id.startsWith(id + '-'));
  } else if (norm(q.topic)) {
    const words = topicWords(q.topic);
    const scored = reqRows.map(r => ({ r, s: words.filter(w => norm(`${r.request_type} ${r.category}`).split(' ').includes(w)).length }))
      .filter(x => x.s > 0);
    const best = Math.max(0, ...scored.map(x => x.s));
    cands = scored.filter(x => x.s === best && best > 0).map(x => x.r);
  } else return { found: false, status: 'needs_input', needs: ['request_id or topic'] };
  if (!cands.length) return { found: false, status: 'not_found' };
  const types = new Set(cands.map(r => r.request_id.replace(/-[A-Z]+$/, '')));
  if (types.size > 1) return { found: false, status: 'ambiguous', candidates: cands.map(r => r.request_id) };
  // regime-split requests (REQ-07-J / REQ-07-SA …): the regime decides, never a guess
  if (cands.length > 1) {
    if (!q.regime) return { found: false, status: 'needs_input', needs: ['regime'], candidates: cands.map(r => r.request_id) };
    cands = cands.filter(r => r.regime === 'all' || r.regime.split(';').includes(q.regime));
    if (cands.length !== 1) return { found: false, status: 'not_found', note: `no single row for regime ${q.regime}` };
  } else if (q.regime && cands[0].regime !== 'all' && !cands[0].regime.split(';').includes(q.regime)) {
    return { found: false, status: 'not_applicable', note: `${cands[0].request_id} applies to ${cands[0].regime}` };
  }
  const row = blankToNull(cands[0]);
  let handler = row.handler_role_id;
  const needs = [];
  if (handler === 'SCO-LEVEL') {
    handler = levelRole(q.class_group);
    if (!handler) needs.push('class_group');
  }
  const contact = handler ? dirRows.find(r => r.role_id === handler) : null;
  return { found: true, status: needs.length ? 'needs_input' : 'found', needs, request: row,
           handler_role_id: handler, contact: contact ? blankToNull(contact) : null,
           escalation_path: handler ? escalation(dirRows, handler) : [],
           is_fictitious: /FICTITIOUS/.test(row.source || '') };
}

// Minimal RFC 4180 CSV parser (quotes, commas and newlines inside quotes) — used by the tests and the table check.
function parseCsv(text) {
  const rows = []; let row = [], cell = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; } else if (c === '"') q = false; else cell += c;
    } else if (c === '"') q = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(cell); rows.push(row); row = []; cell = '';
    } else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const head = rows.shift();
  return rows.filter(r => r.length > 1 || r[0]).map(r => Object.fromEntries(head.map((h, k) => [h, r[k] ?? ''])));
}

if (typeof module !== 'undefined') module.exports = { norm, lookupExam, lookupContact, lookupRequest, parseCsv, levelRole, sessionOf };
