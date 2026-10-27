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

// Same rule for the exam session (CF-409): the local Router invented « Rattrapage » on 4 of 12 T2 questions.
function sessionFromText(text) {
  const t = String(text || '').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase();
  if (/rattrapage|session de controle|\bcontrole\b|session 2|retake|resit/.test(t)) return 'Rattrapage';
  if (/principale|session 1|session normale/.test(t)) return 'Principale';
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

// The model's citation format, repaired in code (CF-807): one reference per bracket, and the demonstration label
// right after each FICTITIOUS reference — removed from official ones. fictifDocs: doc ids retrieved as FICTITIOUS.
const DEMO_LABEL = /\s*\((?:procédure de démonstration|demonstration procedure)\)/gi;
function normalizeCitations(text, fictifDocs, lang) {
  const label = lang === 'en' ? '(demonstration procedure)' : '(procédure de démonstration)';
  const split = String(text ?? '').replace(/\[([^\]]*D1-\d{3}[^\]]*)\]/g, (_, inner) =>
    inner.replace(DEMO_LABEL, '').split(/\s*[;,]\s*(?=D1-\d{3})/).map(p => `[${p.trim()}]`).join(' '));
  return split.replace(DEMO_LABEL, '')
    .replace(/\[(D1-\d{3})[^\]]*\]/g, (m, doc) => (fictifDocs && fictifDocs.has(doc) ? `${m} ${label}` : m));
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

// The student's own records (grades, absences, file) — the only out-of-scope case that names the registrar
function isPersonal(question) {
  const t = String(question ?? '').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase();
  return /\b(ma|mes|mon)\s+(notes?|moyennes?|absences?|dossier|resultats?|bulletin|releve|classement)\b/.test(t);
}

function refusalReply(lang, injection, personal = false) {
  if (lang === 'en') return injection ? 'I cannot change my instructions. I can help with regulations, exam dates and administrative contacts.'
    : 'That is outside what I can help with. I answer questions on school regulations, exam dates and administrative contacts.';
  if (injection) return 'Je ne peux pas modifier mes consignes. Je peux t\'aider sur le règlement, les dates d\'examen et les contacts administratifs.';
  return personal
    ? `Cette demande est hors de mon périmètre (je n'ai pas accès aux dossiers personnels). Je peux t'aider sur le règlement, les dates d'examen et les contacts administratifs ; pour ton dossier, contacte la scolarité (${CONTACT_DEFAULT}).`
    : "Cette demande est hors de mon périmètre. Je réponds sur le règlement de scolarité, les dates d'examen, les bureaux et démarches administratives, et je lis les photos de convocations ou d'emplois du temps. Écris /aide pour des exemples.";
}

// Greetings and commands are answered at once, without the Router (CF-406). A greeting followed by a question is a question.
function smallTalk(text) {
  const t = String(text ?? '').trim().toLowerCase();
  if (!t) return null;
  if (/^\/(reset|nouveau)\b/.test(t)) return 'reset';
  if (t.startsWith('/')) return 'start';
  if (/^(merci|thanks|thank you)(\s+(beaucoup|bien|a toi|à toi))?\s*[!.]*$/.test(t)) return 'thanks';
  if (/^(bonjour|bonsoir|salut|hello|hi|hey|coucou|salam)(\s+\S{1,12})?\s*[!.]*$/.test(t)) return 'start';
  return null;
}

function smallTalkReply(kind, lang) {
  if (kind === 'reset') return "C'est reparti à zéro : j'ai oublié ton régime. Pose ta question (et précise cours du jour, du soir ou alternance si la règle en dépend).";
  if (kind === 'thanks') return 'Avec plaisir ! Une autre question sur le règlement, un examen ou une démarche ?';
  return [
    "👋 Bonjour ! Je suis CampusFlow AI, l'assistant des étudiants d'ESPRIT (projet de cours ; certaines données sont des exemples fictifs, toujours signalés).",
    'Je peux :',
    '• répondre sur le règlement de scolarité, avec la source (document, article, page) ;',
    "• donner la date, l'heure et la salle d'un examen ;",
    "• te dire à quel bureau t'adresser et préparer un brouillon de demande ;",
    "• lire la photo d'une convocation ou d'un emploi du temps.",
    'Exemples :',
    "– « C'est quand l'épreuve d'Advanced Deep Learning pour la classe 5DS6 ? »",
    '– « Cours du jour : si on me surprend en train de tricher pendant un examen, je risque quoi ? »',
    '– « À qui je demande une attestation de scolarité ? Je suis en 4SE1. »',
    'Précise ton régime (cours du jour, du soir ou alternance) : les règles en dépendent. /reset pour repartir à zéro.',
  ].join('\n');
}

// Telegram is sent as HTML: escaping makes it show exactly what we wrote (Markdown ate « [D1-…] »).
function toTelegramHtml(text) {
  return String(text ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// A regime remembered from earlier messages is said, never applied silently.
function regimeRecall(regime, lang) {
  if (!regime || !REGIME_FR[regime]) return '';
  return `ℹ️ Réponse pour le ${REGIME_FR[regime].replace(/^alternance$/, "régime de l'alternance")} (régime retenu de tes messages précédents ; écris /reset pour l'oublier).`;
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

if (typeof module !== 'undefined') module.exports = { normalizeInput, regimeFromText, sessionFromText, parseRouter, decidePaths, photoOnlyReply, ref, regulationsUser,
  citations, normalizeCitations, calendarReply, contactReply, refusalReply, isPersonal, smallTalk, smallTalkReply, toTelegramHtml, regimeRecall, fallbackReply, mergeSections, contractResponse, hashChat, frDate, regimeNote, photoFacts };
