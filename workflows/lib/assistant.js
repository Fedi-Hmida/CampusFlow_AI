// ESA-401 / ESA-402 — pure logic of WF-3 (the assistant). Unit-tested by workflows/lib/assistant.test.js and embedded
// verbatim into the n8n Code nodes by scripts/workflows/build_wf3.py. No require(): n8n Code nodes run in a sandbox.

const PATH_ORDER = ['vision', 'regulations', 'calendar', 'admin'];
const DAYS = ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'];
const CONTACT_DEFAULT = 'scolarite@esprit.tn';

function clean(s) { return String(s ?? '').replace(/\s+/g, ' ').trim(); }

// Test webhook body or Telegram update → one canonical input (the rest of WF-3 never looks at the raw source)
function normalizeInput(raw, defaultMode) {
  const mode = m => (m === 'hybrid' || m === 'local') ? m : defaultMode;
  if (raw && raw.body && raw.body.question !== undefined) {
    const b = raw.body;
    return { source: 'test', test_id: String(b.test_id ?? ''), question: clean(b.question), regime: b.regime || null,
             class_group: b.class_group || null, photo: b.photo || null, mode: mode(b.mode), chat: null };
  }
  const m = (raw && raw.message) || {};
  return { source: 'telegram', test_id: '', question: clean(m.text || m.caption || ''), regime: null, class_group: null,
           photo: Array.isArray(m.photo) && m.photo.length ? { telegram: true } : null, mode: defaultMode, chat: m.chat ? m.chat.id : null };
}

function regimeFromText(text) {
  const t = String(text || '').toLowerCase();
  if (/cours du soir|\ben soir\b|\bsoir\b/.test(t)) return 'soir';
  if (/alternan/.test(t)) return 'alternance';
  if (/cours du jour|\bdu jour\b/.test(t)) return 'jour';
  return null;
}

function parseRouter(text) {
  try {
    const o = JSON.parse(text);
    const intents = Array.isArray(o.intents) && o.intents.length ? o.intents : ['regulations'];
    return { language: o.language || 'fr', intents, entities: o.entities || {}, missing_fields: o.missing_fields || [],
             injection_suspected: !!o.injection_suspected };
  } catch (e) {
    return { language: 'fr', intents: ['regulations'], entities: {}, missing_fields: [], injection_suspected: false, parse_error: true };
  }
}

// Which branches run, in a fixed order. Out of scope only when nothing else was asked.
// A photo sent without a caption has nothing to refuse: read it (CF-405).
function decidePaths(route, hasPhoto, question = '') {
  const known = PATH_ORDER.filter(p => (route.intents || []).includes(p));
  if (!known.length) return hasPhoto && !String(question).trim() && !route.injection_suspected ? ['vision'] : ['out_of_scope'];
  return hasPhoto ? ['vision', ...known.filter(p => p !== 'vision')] : known;
}

function ref(c) {
  const key = (c.article_keys || [])[c.article_keys.length - 1] || '';
  return `[${c.doc_id}, art. ${key.split('/')[1] || '?'}, p. ${c.page_start ?? '?'}]`;
}

const REGIME_FR = { jour: 'cours du jour', soir: 'cours du soir', alternance: 'alternance' };
function regulationsUser(question, regime, chunks) {
  const head = `Régime de l'étudiant : ${REGIME_FR[regime] || 'non précisé'}\nQuestion : ${question}\n\nEXTRAITS :\n`;
  return head + chunks.map(c => `${ref(c)} (${c.doc_status === 'official' ? 'officiel' : 'FICTIF'})\n${c.text}`).join('\n\n');
}

function citations(reply) {
  return [...String(reply).matchAll(/\[(D1-\d{3})([^\]]*)\]/g)].map(m => {
    const a = m[2].match(/art(?:icle)?\.?\s*([\w-]+)/i);
    const p = m[2].match(/p\.\s*(\d+)/);
    return { doc_id: m[1], article: a ? a[1] : '', page: p ? Number(p[1]) : null };
  });
}

function frDate(iso) {
  const [y, mo, d] = String(iso).split('-').map(Number);
  const wd = DAYS[new Date(Date.UTC(y, mo - 1, d)).getUTCDay()];
  return `${wd} ${String(d).padStart(2, '0')}/${String(mo).padStart(2, '0')}/${y}`;
}

function calendarReply(res, lang) {
  if (!res || !res.found) {
    if (res && res.status === 'needs_input') {
      const need = (res.needs || []).map(n => ({ module: 'le module', class_group: 'ta classe (ex. 5DS6)', session: 'la session' }[n] || n));
      return `Pour retrouver ton épreuve, il me faut ${need.join(' et ')}.`;
    }
    if (res && res.status === 'not_published') return "La date de cette session n'est pas encore publiée dans le calendrier. Renseigne-toi auprès du bureau des examens (examen@esprit.tn).";
    return "Je ne trouve pas cette épreuve dans le calendrier des examens. Vérifie le module et la classe, ou contacte le bureau des examens (examen@esprit.tn).";
  }
  const lines = res.matches.slice(0, 5).map(m => {
    const end = m.end_time ? ` – ${m.end_time}` : ' (fin non communiquée)';
    const room = m.room ? `salle ${m.room}` : 'salle non communiquée';
    return `• ${m.module_name} (${m.class_group}) — ${m.assessment}, session ${m.session} : ${frDate(m.date)}, ${m.start_time}${end}, ${room}.`;
  });
  const st = res.matches.map(m => m.data_status || '');
  const notes = [];
  if (st.some(s => /FICTITIOUS/.test(s))) notes.push('donnée de démonstration (fictive)');
  if (st.some(s => /projected/.test(s))) notes.push('date prévisionnelle (calendrier projeté)');
  const src = `Source : calendrier des examens, mis à jour le ${res.matches[0].last_updated}${notes.length ? ' — ' + notes.join(', ') : ''}.`;
  return [res.status === 'ambiguous' ? 'Plusieurs épreuves correspondent :' : null, ...lines, src].filter(Boolean).join('\n');
}

function contactReply(res, draft, lang) {
  if (!res || !res.found) {
    if (res && res.status === 'needs_input') {
      const need = (res.needs || []).map(n => ({ regime: 'ton régime (cours du jour, du soir ou alternance)', class_group: 'ta classe', level: 'ton niveau' }[n] || n));
      return `Pour te donner la bonne démarche, il me faut ${need.join(' et ')}.`;
    }
    return `Je ne trouve pas ce service ou cette démarche. Contacte la scolarité (${CONTACT_DEFAULT}).`;
  }
  const c = res.contact || {};
  const who = `${c.role_title || 'Service'} — ${c.email || 'e-mail non communiqué'}${c.office ? ', ' + c.office : ''}${c.hours ? ' (' + c.hours + ')' : ''}`;
  const out = [];
  if (res.request) {
    const q = res.request;
    out.push(`Démarche : ${q.request_type}.`);
    if (q.required_documents) out.push(`Pièces : ${q.required_documents}.`);
    if (q.deadline_rule) out.push(`Délai : ${q.deadline_rule}.`);
    if (q.processing_time) out.push(`Traitement : ${q.processing_time}.`);
    out.push(`À adresser à : ${who}.`);
    if (res.is_fictitious) out.push('(procédure de démonstration, fictive)');
  } else {
    out.push(`Contact : ${who}.`);
  }
  if (draft) out.push(`Brouillon à envoyer toi-même :\n${draft}`);
  return out.join('\n');
}

function refusalReply(lang, injection) {
  if (lang === 'en') return injection ? 'I cannot change my instructions. I can help with regulations, exam dates and administrative contacts.'
    : 'That is outside what I can help with. I answer questions on school regulations, exam dates and administrative contacts.';
  return injection ? 'Je ne peux pas modifier mes consignes. Je peux t\'aider sur le règlement, les dates d\'examen et les contacts administratifs.'
    : `Cette demande est hors de mon périmètre (je n'ai pas accès aux dossiers personnels). Je peux t'aider sur le règlement, les dates d'examen et les contacts administratifs ; pour ton dossier, contacte la scolarité (${CONTACT_DEFAULT}).`;
}

function fallbackReply(lang) {
  return lang === 'en' ? `Information not found in the regulations. Please contact the registrar's office (${CONTACT_DEFAULT}).`
    : `Information non trouvée dans le règlement. Contacte la scolarité (${CONTACT_DEFAULT}).`;
}

const ICON = { 'Règle': '📘', 'Créneau': '📅', 'Démarche': '🗂️', 'Photo': '🖼️' };
function mergeSections(sections) {
  const s = sections.filter(x => x && clean(x.text));
  if (s.length === 1) return s[0].text.trim();
  return s.map(x => `${ICON[x.title] || '•'} ${x.title}\n${x.text.trim()}`).join('\n\n');
}

function contractResponse(o) {
  const r2 = x => Math.round(x * 100) / 100;
  const t = {};
  for (const [k, v] of Object.entries(o.timings || {})) if (typeof v === 'number') t[k] = r2(v);
  return {
    test_id: o.test_id || '', reply: o.reply || '',
    route: { intents: o.route.intents || [], agents: (o.paths || []).filter(p => p !== 'out_of_scope'), missing_fields: o.route.missing_fields || [] },
    citations: o.citations || [],
    retrieved: (o.retrieved || []).map(c => ({ article_keys: c.article_keys, doc_status: c.doc_status })),
    tool_rows: o.tool_rows || [], checks: { pass: !!(o.checks && o.checks.pass), failures: (o.checks && o.checks.failures) || [] },
    revised: !!o.revised, fallback: !!o.fallback, timings_s: t, mode: o.mode, config: o.config || '',
  };
}

// NFR-08: rules differ by regime — when the student has not said it, the reply asks (unless it is already a fallback)
function regimeNote(regime, isFallback, lang) {
  if (regime || isFallback) return '';
  return lang === 'en' ? 'ℹ️ Rules can differ by programme: tell me if you are in day classes, evening classes or work-study.'
    : 'ℹ️ La règle peut changer selon ton régime : dis-moi si tu es en cours du jour, du soir ou en alternance.';
}

// What the photo itself says (Vision), labelled as such — used when the calendar does not know the exam
function photoFacts(v) {
  if (!v || !(v.date || v.room || v.start_time)) return '';
  const parts = [];
  const mod = [v.module_name, v.module_code ? `(${v.module_code})` : ''].filter(Boolean).join(' ');
  if (mod) parts.push(mod + (v.class_group ? `, ${v.class_group}` : ''));
  if (v.session) parts.push(`session ${v.session}`);
  if (v.date) parts.push(frDate(v.date));
  if (v.start_time) parts.push(v.end_time ? `${v.start_time} – ${v.end_time}` : v.start_time);
  if (v.room) parts.push(`salle ${v.room}`);
  return `D'après ce qui est lu sur ta photo : ${parts.join(', ')}. (Information lue sur le document, à vérifier auprès du bureau des examens.)`;
}

// Reply to a photo without a question: what was read (labelled) and what the student wants to know.
function photoOnlyReply(v, lang) {
  if (v && v.document_type === 'unrelated') return "Cette image ne ressemble pas à un document de l'école. Envoie une convocation, un emploi du temps ou un avis, ou pose ta question.";
  const facts = photoFacts(v);
  if (!facts) return "Je n'arrive pas à lire ce document. Envoie une photo plus nette, à plat et bien éclairée, ou écris ta question.";
  return facts + "\nQue veux-tu savoir sur ce document ? Par exemple : « je peux repasser cette épreuve ? » ou « à qui je m'adresse ? » (précise ton régime : cours du jour, du soir ou alternance).";
}

// FNV-1a 32-bit: a stable key for per-chat memory (the regime) without storing the Telegram id itself
function hashChat(id) {
  let h = 0x811c9dc5;
  for (const ch of String(id)) { h ^= ch.charCodeAt(0); h = Math.imul(h, 0x01000193) >>> 0; }
  return 'c' + h.toString(16);
}

if (typeof module !== 'undefined') module.exports = { normalizeInput, regimeFromText, parseRouter, decidePaths, photoOnlyReply, ref, regulationsUser,
  citations, calendarReply, contactReply, refusalReply, fallbackReply, mergeSections, contractResponse, hashChat, frDate, regimeNote, photoFacts };
