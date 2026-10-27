// CF-010 — deterministic Critic (ADR-010): checks a reply against the evidence the specialists used, in milliseconds,
// instead of a ~70 s LLM call on CPU. Pure function, unit-tested by workflows/lib/checks.test.js; embedded in WF-3.
//   citation_present   a substantive reply cites at least one [D1-xxx, art. N, p. P]
//   citation_retrieved every cited (document, article) was among the retrieved chunks
//   facts_grounded     every date, time, room, e-mail and delay in the reply appears in the evidence
//   fictif_labelled    a reply that cites a FICTITIOUS document says so (fictif / démonstration)
//   not_sent           the bot never claims it sent something for the student
//   not_found_contact  a « not found » reply gives a contact
// Result: { pass, failures: [{ check, detail }] } — n8n sends on pass, else one revision, else a safe fallback.


function fold(s) {
  return String(s ?? '').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

// Canonical forms so « 15/01/2027 » = « 2027-01-15 », « 9h00 » = « 09:00 », « 48 heures » = « 48 h »
function facts(text) {
  const t = fold(text);
  const out = [];
  for (const m of t.matchAll(/\b(\d{1,2})\/(\d{1,2})\/(\d{4})\b/g)) out.push(`date:${m[3]}-${m[2].padStart(2, '0')}-${m[1].padStart(2, '0')}`);
  for (const m of t.matchAll(/\b(\d{4})-(\d{2})-(\d{2})\b/g)) out.push(`date:${m[1]}-${m[2]}-${m[3]}`);
  for (const m of t.matchAll(/\b(\d{1,2})\s*[h:]\s*(\d{2})\b/g)) out.push(`time:${m[1].padStart(2, '0')}:${m[2]}`);
  for (const m of t.matchAll(/\bsalle\s+([a-h]\d{2})\b/g)) out.push(`room:${m[1]}`);
  for (const m of t.matchAll(/[\w.+-]+@[\w-]+(?:\.[\w-]+)+/g)) out.push(`mail:${m[0]}`);
  for (const m of t.matchAll(/\b(\d+)\s*(h|heures?|jours?|semaines?|mois)\b/g)) {
    const unit = m[2].startsWith('h') ? 'h' : m[2].startsWith('jour') ? 'jour' : m[2].startsWith('sem') ? 'semaine' : 'mois';
    out.push(`delay:${m[1]}${unit}`);
  }
  return out;
}

function citedRefs(reply) {   // not « citations »: assistant.js has one and both share a Code node (CF-404)
  return [...reply.matchAll(/\[(D1-\d{3})([^\]]*)\]/g)].map(m => {
    const art = m[2].match(/art(?:icle)?\.?\s*([\w-]+)/i);
    return { doc: m[1], article: art ? art[1] : null, raw: m[0] };
  });
}

// allowed: facts the reply may contain without being in the excerpts — the directory e-mails the prompts name
// (e.g. scolarite@esprit.tn for « not found ») and the values returned by the lookup tools.
function checkReply(reply, { retrieved = [], allowed = [] } = {}) {
  const failures = [];
  const add = (check, detail) => failures.push({ check, detail });
  const text = String(reply ?? '').trim();
  if (!text) return { pass: false, failures: [{ check: 'empty', detail: 'empty reply' }] };

  const notFound = /non trouv|introuvable|not found/i.test(fold(text));
  const cites = citedRefs(text);
  if (!cites.length && !notFound) add('citation_present', 'no [D1-xxx, art. N] citation');

  const keys = retrieved.flatMap(c => c.article_keys || []);
  for (const c of cites) {
    const hit = keys.some(k => { const [d, n] = k.split('/'); return d === c.doc && (!c.article || n === c.article); });
    if (!hit) add('citation_retrieved', `${c.raw} not among the retrieved chunks`);
  }

  const evidence = new Set(facts(retrieved.map(c => c.text).concat(allowed).join('\n')));
  const body = text.replace(/\[D1-\d{3}[^\]]*\]/g, ' ');           // page / article numbers are not facts
  const missing = facts(body).filter(f => !evidence.has(f));
  if (missing.length) add('facts_grounded', `not in the evidence: ${[...new Set(missing)].join(', ')}`);

  const fictifDocs = new Set(retrieved.filter(c => c.doc_status === 'FICTITIOUS').flatMap(c => (c.article_keys || []).map(k => k.split('/')[0])));
  if (cites.some(c => fictifDocs.has(c.doc)) && !/fictif|fictive|demonstration|fictitious/.test(fold(text))) {
    add('fictif_labelled', 'cites a FICTITIOUS document without saying so');
  }

  if (/(j'ai|je l'ai|nous avons|a ete|ont ete)\s+(envoy|transmi)/.test(fold(text))) add('not_sent', 'claims something was sent');

  if (notFound && !/[\w.+-]+@[\w-]+\.[\w.-]+/.test(text)) add('not_found_contact', '« not found » without a contact');

  return { pass: failures.length === 0, failures };
}

if (typeof module !== 'undefined') module.exports = { checkReply, facts, citedRefs };
