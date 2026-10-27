"""ESA-401 / ESA-402 — generate the assistant workflows from tested code, prompts and config/agents.json.

  workflows/20_llm_call.json      sub-workflow: one LLM call, provider "gemini" (n8n credential) or "ollama" (local),
                                  optional JSON schema / JSON mode, optional image; returns {text, provider, seconds, tokens}
  workflows/03_wf3_assistant.json the assistant: Telegram trigger + test webhook (eval/e2e/CONTRACT.md) → input → (ack) →
                                  Router (local) → refusal | vision → regulations (B official-first, checks, 1 revision,
                                  fallback) → calendar (tool) → admin (tools + optional draft) → merge → reply / JSON
Everything the Code nodes run is embedded from workflows/lib/assistant.js, checks.js (unit-tested); prompts come from
prompts/P-*.md at the versions named in config/agents.json; models from its providers. State travels in item.json.state.
Run: .venv/Scripts/python -X utf8 scripts/workflows/build_wf3.py   (then import + publish, see eval/e2e/CONTRACT.md)
"""
import csv
import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "workflows"
CFG = json.loads((ROOT / "config/agents.json").read_text(encoding="utf-8"))
ASSISTANT = (W / "lib/assistant.js").read_text(encoding="utf-8")
CHECKS = (W / "lib/checks.js").read_text(encoding="utf-8")
NS = uuid.UUID("5b8f1c2e-3d4a-4e6b-9c7d-1f2e3a4b5c6d")
LLM_ID, WF3_ID, WF4_ID = "cfLLMCall0000001", "cfWF3Assistant01", "cfWF4Errors00001"
TOOLS = {"exam": "cfToolExam000001", "contact": "cfToolContact001", "request": "cfToolRequest001"}
TG = {"telegramApi": {"id": "cfTelegramBot001", "name": "Telegram CampusFlowAI_bot"}}
GEM = {"googlePalmApi": {"id": "cfGeminiApi00001", "name": "Google Gemini API"}}


def template(agent_prompt: str) -> str:
    pid, ver = agent_prompt.split("@")
    text = (ROOT / f"prompts/{pid}.md").read_text(encoding="utf-8")
    return re.search(r"<!-- template:" + ver + r" -->\s*```text\n(.*?)\n```", text, re.S).group(1)


A = CFG["agents"]
LOCAL = CFG["providers"]["local"]
PROMPTS = {"router": template(A["router"]["prompt"]), "vision": template(A["vision"]["prompt"]),
           "regulations": template(A["regulations"]["prompt"])}
ROUTER_SCHEMA = json.loads((ROOT / A["router"]["schema"]).read_text(encoding="utf-8"))
SHOTS = []
for e in json.loads((ROOT / A["router"]["examples"]).read_text(encoding="utf-8"))["examples"]:
    SHOTS += [{"role": "user", "content": json.dumps({"message": e["message"], "has_photo": e["has_photo"]}, ensure_ascii=False)},
              {"role": "assistant", "content": json.dumps(e["output"], ensure_ascii=False)}]
EMAILS = [r["email"] for r in csv.DictReader(open(ROOT / "data/tables/directory.csv", encoding="utf-8"))]
CONFIG_TAG = f"router {A['router']['prompt'].split('@')[1]} · regulations {A['regulations']['prompt'].split('@')[1]} · vision {A['vision']['prompt'].split('@')[1]}"
CONSTS = ("const CFG = " + json.dumps({"mode": CFG["mode"], "ack": CFG["latency"]["ack_message_fr"], "ack_local": CFG["latency"]["ack_message_fr_local"],
                                        "local_model": LOCAL["model"], "keep_alive": LOCAL["keep_alive"], "config": CONFIG_TAG,
                                        "retrieval": A["regulations"]["retrieval"]}, ensure_ascii=False) + ";\n")


def nid(wf: str, name: str) -> str:
    return str(uuid.uuid5(NS, f"{wf}/{name}"))


def node(wf, name, type_, version, pos, params, **extra):
    return {"id": nid(wf, name), "name": name, "type": type_, "typeVersion": version, "position": pos, "parameters": params, **extra}


def top_names(js: str) -> set:
    return set(re.findall(r"^(?:function|const|let|var)\s+([A-Za-z_$][\w$]*)", js, re.M))


def code(wf, name, pos, js, libs=()):
    # libs share one scope: a name defined twice would silently shadow the first (CF-404: citations())
    seen = {}
    for i, part in enumerate([*libs, js]):
        for n in top_names(part):
            assert n not in seen, f"{wf}/{name}: '{n}' defined in embedded parts {seen[n]} and {i}"
            seen[n] = i
    return node(wf, name, "n8n-nodes-base.code", 2, pos, {"jsCode": "".join(l + "\n" for l in libs) + js})


def http(wf, name, pos, url, body_expr, timeout=120000, creds=None, method="POST"):
    p = {"method": method, "url": url, "sendBody": True, "specifyBody": "json", "jsonBody": body_expr, "options": {"timeout": timeout}}
    extra = {"retryOnFail": True, "maxTries": 3, "waitBetweenTries": 5000}
    if creds:
        p.update({"authentication": "predefinedCredentialType", "nodeCredentialType": "googlePalmApi"})
        extra["credentials"] = creds
    return node(wf, name, "n8n-nodes-base.httpRequest", 4.2, pos, p, **extra)


def call_wf(wf, name, pos, target):
    return node(wf, name, "n8n-nodes-base.executeWorkflow", 1.2, pos,
                {"source": "database", "workflowId": {"__rl": True, "mode": "id", "value": target}, "mode": "once",
                 "options": {"waitForSubWorkflow": True}})


def iff(wf, name, pos, js_condition):
    return node(wf, name, "n8n-nodes-base.if", 2.2, pos, {
        "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                       "conditions": [{"id": nid(wf, name + "/c"), "leftValue": "={{ " + js_condition + " }}", "rightValue": "",
                                       "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                       "combinator": "and"}, "options": {}})


# --------------------------------------------------------------------------------------------- 20_llm_call
LLM_PREP = r"""
// One LLM call. Input: item.json.llm = {provider, system, user, messages?, schema?, json?, max_tokens, temperature, image_b64?, image_mime?}
const L = $input.first().json.llm;
if (!L) throw new Error('20_llm_call: missing llm parameters');
const t0 = Date.now();
if (L.provider === 'gemini') {
  const parts = [{ text: L.user }];
  if (L.image_b64) parts.push({ inline_data: { mime_type: L.image_mime || 'image/jpeg', data: L.image_b64 } });
  const cfg = { temperature: L.temperature ?? 0.1, maxOutputTokens: L.max_tokens ?? 200 };
  if (L.json) cfg.responseMimeType = 'application/json';
  const body = { contents: [{ role: 'user', parts }], generationConfig: cfg };
  if (L.system) body.systemInstruction = { parts: [{ text: L.system }] };
  return [{ json: { provider: 'gemini', body, t0 } }];
}
const msgs = L.messages || [...(L.system ? [{ role: 'system', content: L.system }] : []), { role: 'user', content: L.user }];
if (L.image_b64) msgs[msgs.length - 1].images = [L.image_b64];
const body = { model: CFG.local_model, messages: msgs, stream: false, keep_alive: CFG.keep_alive,
               options: { temperature: L.temperature ?? 0, num_predict: L.max_tokens ?? 200 } };
if (L.schema) body.format = L.schema; else if (L.json) body.format = 'json';
return [{ json: { provider: 'ollama', body, t0 } }];
"""
LLM_OUT = r"""
const prep = $('Prepare').first().json;
const r = $input.first().json;
let text = '', pt = null, ot = null;
if (prep.provider === 'gemini') {
  text = (((r.candidates || [])[0] || {}).content || { parts: [{ text: '' }] }).parts.map(p => p.text || '').join('');
  pt = (r.usageMetadata || {}).promptTokenCount ?? null; ot = (r.usageMetadata || {}).candidatesTokenCount ?? null;
} else {
  text = (r.message || {}).content || ''; pt = r.prompt_eval_count ?? null; ot = r.eval_count ?? null;
}
return [{ json: { text: text.trim(), provider: prep.provider, seconds: (Date.now() - prep.t0) / 1000, prompt_tokens: pt, output_tokens: ot } }];
"""


def llm_workflow():
    wf = "llm"
    nodes = [
        node(wf, "When called", "n8n-nodes-base.executeWorkflowTrigger", 1.1, [0, 300], {"inputSource": "passthrough"}),
        code(wf, "Prepare", [220, 300], LLM_PREP, [CONSTS]),
        iff(wf, "Gemini?", [440, 300], "$json.provider === 'gemini'"),
        http(wf, "Gemini", [660, 200], f"https://generativelanguage.googleapis.com/v1beta/models/{CFG['providers']['gemini']['model']}:generateContent",
             "={{ JSON.stringify($json.body) }}", 60000, GEM),
        http(wf, "Ollama", [660, 420], "http://ollama:11434/api/chat", "={{ JSON.stringify($json.body) }}", 600000),
        code(wf, "Result", [880, 300], LLM_OUT),
    ]
    conn = {"When called": {"main": [[{"node": "Prepare", "type": "main", "index": 0}]]},
            "Prepare": {"main": [[{"node": "Gemini?", "type": "main", "index": 0}]]},
            "Gemini?": {"main": [[{"node": "Gemini", "type": "main", "index": 0}], [{"node": "Ollama", "type": "main", "index": 0}]]},
            "Gemini": {"main": [[{"node": "Result", "type": "main", "index": 0}]]},
            "Ollama": {"main": [[{"node": "Result", "type": "main", "index": 0}]]}}
    return [{"id": LLM_ID, "name": "20_llm_call", "active": False,
             "settings": {"executionOrder": "v1", "callerPolicy": "workflowsFromSameOwner"}, "nodes": nodes, "connections": conn,
             "pinData": {}, "tags": []}]


# --------------------------------------------------------------------------------------------- 03_wf3_assistant
J = lambda o: json.dumps(o, ensure_ascii=False)  # noqa: E731

INPUT = r"""
// Canonical input from either trigger; per-chat regime memory keyed by a hash (no Telegram id stored)
const raw = $input.first();
// test-only hook to prove the error path (WF-4); honoured only on the test entrance, never from Telegram
if (raw.json.body && raw.json.body.force_error === 'smoke') throw new Error('forced error (smoke test of WF-4)');
const inp = normalizeInput(raw.json, CFG.mode);
const state = { input: inp, t0: Date.now(), timings: {}, sections: [], tool_rows: [], retrieved: [], citations: [],
                checks: { pass: true, failures: [] }, revised: false, fallback: false };
if (inp.source === 'telegram') {
  const mem = $getWorkflowStaticData('global');
  mem.regimes = mem.regimes || {};
  const key = hashChat(inp.chat);
  const said = regimeFromText(inp.question);
  if (smallTalk(inp.question) === 'reset') delete mem.regimes[key];
  else if (said) mem.regimes[key] = said;
  inp.regime = said || mem.regimes[key] || null;
  inp.regime_from = said ? 'message' : inp.regime ? 'memory' : null;
  if (raw.binary && Object.keys(raw.binary).length) {
    const k = Object.keys(raw.binary)[0];
    const buf = await this.helpers.getBinaryDataBuffer(0, k);
    state.image = { b64: buf.toString('base64'), mime: raw.binary[k].mimeType || 'image/jpeg' };
  }
} else if (!inp.regime) {
  inp.regime = regimeFromText(inp.question);
}
state.small = inp.photo ? null : smallTalk(inp.question);   // greeting / command: answered without the Router (CF-406)
state.ack = inp.mode === 'local' ? CFG.ack_local : CFG.ack;
return [{ json: { state } }];
"""
TEST_PHOTO = r"""
// Test photo read from /t4 (eval/testsets/T4_photos, read-only mount) → base64 into the state
const state = $('Input').first().json.state;
const buf = await this.helpers.getBinaryDataBuffer(0, 'data');
const name = state.input.photo.file || '';
state.image = { b64: buf.toString('base64'), mime: /\.png$/i.test(name) ? 'image/png' : 'image/jpeg' };
return [{ json: { state } }];
"""
ROUTER_REQ = r"""
const state = $json.state || $('Input').first().json.state;
state.tr = Date.now();
const msg = JSON.stringify({ message: state.input.question, has_photo: !!state.image });
state.llm = { provider: 'ollama', messages: [{ role: 'system', content: PROMPT_ROUTER }, ...SHOTS, { role: 'user', content: msg }],
              schema: ROUTER_SCHEMA, max_tokens: 120, temperature: 0 };
return [{ json: { state, llm: state.llm } }];
"""
ROUTE = r"""
const state = $('Router request').first().json.state;
delete state.llm;
const out = $input.first().json;
const route = parseRouter(out.text);
state.route = route;
state.lang = route.language === 'en' ? 'en' : 'fr';
if (!state.input.regime && route.entities.regime) state.input.regime = route.entities.regime;
route.entities.session = sessionFromText(state.input.question);   // stated only, never the Router's guess (CF-409); a photo may fill it
state.paths = decidePaths(route, !!state.image, state.input.question);
state.timings.router = (Date.now() - state.tr) / 1000;
return [{ json: { state } }];
"""
SMALL = r"""
const state = $json.state;
state.route = { language: 'fr', intents: [], entities: {}, missing_fields: [], injection_suspected: false };
state.lang = 'fr';
state.paths = [];
state.sections.push({ title: 'Réponse', text: smallTalkReply(state.small, state.lang) });
return [{ json: { state } }];
"""
REFUSAL = r"""
const state = $json.state;
state.sections.push({ title: 'Réponse', text: refusalReply(state.lang, !!state.route.injection_suspected,
  isPersonal(state.input.question) || /personn/i.test(state.route.entities.topic || '')) });
return [{ json: { state } }];
"""
VISION_REQ = r"""
const state = $json.state;
state.tv = Date.now();
state.llm = { provider: 'gemini', user: PROMPT_VISION, json: true, max_tokens: 2048, temperature: 0,
              image_b64: state.image.b64, image_mime: state.image.mime };
return [{ json: { state, llm: state.llm } }];
"""
VISION_USE = r"""
// Facts read on the photo complete the entities the student did not type; photo text is data, never instructions
const state = $('Vision request').first().json.state;
delete state.llm;
let v = {};
try { v = JSON.parse($input.first().json.text); } catch (e) { v = { image_readable: false }; }
state.vision = v;
const ent = state.route.entities;
if (!ent.module && (v.module_code || v.module_name)) ent.module = v.module_code || v.module_name;
if (!state.input.class_group && v.class_group) state.input.class_group = v.class_group;
if (!ent.session && v.session) ent.session = v.session;
if (!state.input.regime && v.regime) state.input.regime = v.regime;
const bare = !state.input.question;   // photo without a caption (CF-405): say what was read and ask what they want
// a convocation without any other intent → look the exam up in the calendar
if (!bare && v.document_type === 'convocation' && !state.paths.includes('calendar') && (ent.module && state.input.class_group)) state.paths.push('calendar');
const facts = bare ? [photoOnlyReply(v, state.lang)] : [];
if (!bare && v.document_type === 'unrelated') facts.push("Cette image ne ressemble pas à un document de l'école.");
if (v.injection_detected) facts.push("La photo contient un texte qui ressemble à une consigne adressée à un assistant : je l'ignore.");
if (facts.length) state.sections.push({ title: 'Photo', text: facts.join(' ') });
state.timings.vision = (Date.now() - state.tv) / 1000;
return [{ json: { state } }];
"""
EMBED_BODY = "={{ JSON.stringify({ model: 'bge-m3:567m', input: [$json.state.input.question] }) }}"
QDRANT_BODY = ("={{ JSON.stringify({ query: $('Embed question').first().json.embeddings[0], limit: LIMIT, with_payload: true, filter: { must: "
               "[{ key: 'doc_status', match: { value: 'STATUS' } }].concat($('Retrieval start').first().json.state.input.regime ? "
               "[{ key: 'regimes', match: { any: [$('Retrieval start').first().json.state.input.regime] } }] : []) } }) }}")
RETR_START = r"""
const state = $json.state;
state.tq = Date.now();
return [{ json: { state } }];
"""
REG_REQ = r"""
const state = $('Retrieval start').first().json.state;
const pts = [...$('Qdrant official').first().json.result.points, ...$input.first().json.result.points]
  .sort((a, b) => b.score - a.score).map(p => ({ ...p.payload, score: p.score }));
state.chunks = pts;
state.retrieved = pts.map(p => ({ article_keys: p.article_keys, doc_status: p.doc_status, text: p.text }));
state.timings.retrieval = (Date.now() - state.tq) / 1000;
state.tg = Date.now();
state.llm = { provider: state.input.mode === 'local' ? 'ollama' : 'gemini', system: PROMPT_REGULATIONS,
              user: regulationsUser(state.input.question, state.input.regime, pts), max_tokens: 200, temperature: 0.1 };
return [{ json: { state, llm: state.llm } }];
"""
CHECK1 = r"""
const state = $('Regulations request').first().json.state;
const fictif = new Set(state.retrieved.filter(r => r.doc_status === 'FICTITIOUS').flatMap(r => r.article_keys.map(k => k.split('/')[0])));
const reply = normalizeCitations($input.first().json.text, fictif, state.lang);   // format repaired in code (CF-807)
const c = checkReply(reply, { retrieved: state.retrieved, allowed: EMAILS });
state.draft = reply;
state.checks = { pass: c.pass, failures: c.failures.map(f => f.check) };
state.check_detail = c.failures.map(f => f.check + ': ' + f.detail).join(' ; ');
return [{ json: { state } }];
"""
REVISE = r"""
const state = $json.state;
state.revised = true;
state.llm = { ...state.llm, user: state.llm.user + "\n\nTA RÉPONSE PRÉCÉDENTE :\n" + state.draft +
  "\n\nELLE A ÉCHOUÉ AUX CONTRÔLES : " + state.check_detail + "\nRéécris-la en corrigeant uniquement ces points, sans rien ajouter qui ne soit dans les extraits." };
return [{ json: { state, llm: state.llm } }];
"""
CHECK2 = r"""
const state = $('Revision request').first().json.state;
const fictif = new Set(state.retrieved.filter(r => r.doc_status === 'FICTITIOUS').flatMap(r => r.article_keys.map(k => k.split('/')[0])));
const reply = normalizeCitations($input.first().json.text, fictif, state.lang);   // format repaired in code (CF-807)
const c = checkReply(reply, { retrieved: state.retrieved, allowed: EMAILS });
state.checks = { pass: c.pass, failures: c.failures.map(f => f.check) };
if (c.pass) state.draft = reply; else { state.draft = fallbackReply(state.lang); state.fallback = true; }
return [{ json: { state } }];
"""
REG_SECTION = r"""
const state = $json.state;
delete state.llm; delete state.check_detail;
state.timings.regulations = (Date.now() - state.tg) / 1000;
state.citations = citations(state.draft);
const note = regimeNote(state.input.regime, state.fallback, state.lang);   // also after « non trouvée »: the regime often decides
const recall = state.input.regime_from === 'memory' && !state.fallback ? regimeRecall(state.input.regime, state.lang) : '';
const body = note ? state.draft + '\n' + note : state.draft;
state.sections.push({ title: 'Règle', text: recall ? recall + '\n' + body : body });
delete state.chunks;
return [{ json: { state } }];
"""
CAL_REQ = r"""
const state = $json.state;
state.tc = Date.now();
const e = state.route.entities;
return [{ json: { state, query: { module: e.module || null, class_group: state.input.class_group || e.class_group || null, session: e.session || null } } }];
"""
CAL_USE = r"""
const state = $('Calendar request').first().json.state;
const res = $input.first().json;
state.tool_rows.push(...((res.matches || []).slice(0, 5)));
const seen = !res.found ? photoFacts(state.vision) : '';
state.sections.push({ title: 'Créneau', text: calendarReply(res, state.lang) + (seen ? '\n' + seen : '') });
state.timings.tools = (state.timings.tools || 0) + (Date.now() - state.tc) / 1000;
return [{ json: { state } }];
"""
ADMIN_REQ = r"""
const state = $json.state;
state.ta = Date.now();
const e = state.route.entities;
const topic = e.request || e.topic || state.input.question;
return [{ json: { state, query: { topic, regime: state.input.regime || null, class_group: state.input.class_group || e.class_group || null } } }];
"""
ADMIN_CONTACT = r"""
// No catalogue row matched → look for the office by topic in the directory
const state = $('Admin request').first().json.state;
const req = $input.first().json;
state.admin_request = req;
const e = state.route.entities;
return [{ json: { state, query: req.found || req.status === 'needs_input' ? { role_id: 'NONE' } : { topic: e.topic || e.request || state.input.question } } }];
"""
ADMIN_USE = r"""
const state = $('Admin contact').first().json.state;
const req = state.admin_request;
const contact = $input.first().json;
const res = (req.found || req.status === 'needs_input') ? req : contact;
delete state.admin_request;
if (res.request) state.tool_rows.push(res.request);
if (res.contact) state.tool_rows.push(res.contact);
state.admin_res = res;
state.wants_draft = /r[ée]dig|brouillon|message|mail|e-mail|écri(s|re)/i.test(state.input.question) && !!res.found;
return [{ json: { state } }];
"""
DRAFT_REQ = r"""
const state = $json.state;
const r = state.admin_res;
const facts = JSON.stringify({ demarche: r.request ? r.request.request_type : null, pieces: r.request ? r.request.required_documents : null,
  destinataire: r.contact ? r.contact.email : null, service: r.contact ? r.contact.role_title : null });
state.llm = { provider: state.input.mode === 'local' ? 'ollama' : 'gemini',
  system: "Tu rédiges un court e-mail (5 lignes maximum) que l'étudiant enverra lui-même au service indiqué. N'utilise que les faits donnés ; laisse [Nom], [Classe] à compléter ; n'invente ni délai ni pièce ; ne dis jamais que le message a été envoyé.",
  user: 'Demande de l\'étudiant : ' + state.input.question + '\nFaits : ' + facts, max_tokens: 160, temperature: 0.3 };
return [{ json: { state, llm: state.llm } }];
"""
ADMIN_SECTION = r"""
const state = $json.state || $('Admin result').first().json.state;
let draft = null;
try { const d = $('Draft message').first().json.text; if (state.wants_draft && d) draft = d; } catch (e) { /* no draft requested */ }
state.sections.push({ title: 'Démarche', text: contactReply(state.admin_res, draft, state.lang) });
delete state.admin_res; delete state.llm;
state.timings.admin = (Date.now() - state.ta) / 1000;
return [{ json: { state } }];
"""
OUTPUT = r"""
const state = $json.state;
state.timings.total = (Date.now() - state.t0) / 1000;
const reply = mergeSections(state.sections) || fallbackReply(state.lang);
const response = contractResponse({ test_id: state.input.test_id, reply, route: state.route || { intents: [], missing_fields: [] },
  paths: state.paths || [], citations: state.citations, retrieved: state.retrieved, tool_rows: state.tool_rows, checks: state.checks,
  revised: state.revised, fallback: state.fallback, timings: state.timings, mode: state.input.mode, config: CFG.config });
return [{ json: { response, reply, reply_tg: toTelegramHtml(reply), source: state.input.source, chat: state.input.chat } }];
"""

ROUTER_CONSTS = ("const PROMPT_ROUTER = " + J(PROMPTS["router"]) + ";\nconst SHOTS = " + J(SHOTS) + ";\nconst ROUTER_SCHEMA = " + J(ROUTER_SCHEMA) + ";\n")
REG_CONSTS = "const PROMPT_REGULATIONS = " + J(PROMPTS["regulations"]) + ";\n"
VIS_CONSTS = "const PROMPT_VISION = " + J(PROMPTS["vision"]) + ";\n"
EMAIL_CONSTS = "const EMAILS = " + J(EMAILS) + ";\n"


def wf3_workflow():
    wf = "wf3"
    R = CFG["agents"]["regulations"]["retrieval"]
    q_off = QDRANT_BODY.replace("LIMIT", str(R["official"])).replace("STATUS", "official")
    q_fic = QDRANT_BODY.replace("LIMIT", str(R["fictitious"])).replace("STATUS", "FICTITIOUS")
    n = [
        node(wf, "When called", "n8n-nodes-base.executeWorkflowTrigger", 1.1, [0, 300], {"inputSource": "passthrough"}),
        code(wf, "Input", [220, 300], INPUT, [CONSTS, ASSISTANT]),
        iff(wf, "Small talk?", [440, 300], "!!$json.state.small"),
        code(wf, "Small talk reply", [660, 160], SMALL, [ASSISTANT]),
        iff(wf, "Test photo?", [660, 420], "!!($json.state.input.photo && $json.state.input.photo.file)"),
        node(wf, "Read test photo", "n8n-nodes-base.readWriteFile", 1.1, [880, 360],
             {"operation": "read", "fileSelector": "=/t4/{{ $json.state.input.photo.file }}", "options": {}}),
        code(wf, "Test photo", [1100, 360], TEST_PHOTO),
        code(wf, "Router request", [1320, 300], ROUTER_REQ, [ROUTER_CONSTS]),
        call_wf(wf, "Router", [1540, 300], LLM_ID),
        code(wf, "Route", [1760, 300], ROUTE, [ASSISTANT]),
        iff(wf, "Out of scope?", [1980, 300], "$json.state.paths[0] === 'out_of_scope'"),
        code(wf, "Refusal", [2200, 160], REFUSAL, [ASSISTANT]),
        iff(wf, "Vision?", [2200, 400], "$json.state.paths.includes('vision')"),
        code(wf, "Vision request", [2420, 320], VISION_REQ, [VIS_CONSTS]),
        call_wf(wf, "Vision", [2640, 320], LLM_ID),
        code(wf, "Vision facts", [2860, 320], VISION_USE, [ASSISTANT]),
        iff(wf, "Regulations?", [3080, 400], "$json.state.paths.includes('regulations')"),
        code(wf, "Retrieval start", [3300, 320], RETR_START),
        http(wf, "Embed question", [3520, 320], "http://ollama:11434/api/embed", EMBED_BODY, 60000),
        http(wf, "Qdrant official", [3740, 320], "http://qdrant:6333/collections/regs_structured/points/query", q_off, 30000),
        http(wf, "Qdrant fictitious", [3960, 320], "http://qdrant:6333/collections/regs_structured/points/query", q_fic, 30000),
        code(wf, "Regulations request", [4180, 320], REG_REQ, [CONSTS, REG_CONSTS, ASSISTANT]),
        call_wf(wf, "Regulations", [4400, 320], LLM_ID),
        code(wf, "Checks", [4620, 320], CHECK1, [EMAIL_CONSTS, CHECKS, ASSISTANT]),
        iff(wf, "Checks failed?", [4840, 320], "!$json.state.checks.pass"),
        code(wf, "Revision request", [5060, 240], REVISE),
        call_wf(wf, "Revision", [5280, 240], LLM_ID),
        code(wf, "Checks again", [5500, 240], CHECK2, [EMAIL_CONSTS, CHECKS, ASSISTANT]),
        code(wf, "Regulations section", [5720, 320], REG_SECTION, [ASSISTANT]),
        iff(wf, "Calendar?", [5940, 400], "$json.state.paths.includes('calendar')"),
        code(wf, "Calendar request", [6160, 320], CAL_REQ),
        call_wf(wf, "Exam lookup", [6380, 320], TOOLS["exam"]),
        code(wf, "Calendar section", [6600, 320], CAL_USE, [ASSISTANT]),
        iff(wf, "Admin?", [6820, 400], "$json.state.paths.includes('admin')"),
        code(wf, "Admin request", [7040, 320], ADMIN_REQ),
        call_wf(wf, "Request lookup", [7260, 320], TOOLS["request"]),
        code(wf, "Admin contact", [7480, 320], ADMIN_CONTACT),
        call_wf(wf, "Contact lookup", [7700, 320], TOOLS["contact"]),
        code(wf, "Admin result", [7920, 320], ADMIN_USE),
        iff(wf, "Draft wanted?", [8140, 320], "$json.state.wants_draft"),
        code(wf, "Draft request", [8360, 240], DRAFT_REQ),
        call_wf(wf, "Draft message", [8580, 240], LLM_ID),
        code(wf, "Admin section", [8800, 320], ADMIN_SECTION, [ASSISTANT]),
        code(wf, "Output", [9020, 400], OUTPUT, [CONSTS, ASSISTANT]),
    ]
    links = [("When called", "Input"), ("Input", "Small talk?"), ("Small talk?", "Small talk reply", 0),
             ("Small talk?", "Test photo?", 1), ("Small talk reply", "Output"),
             ("Test photo?", "Read test photo", 0), ("Test photo?", "Router request", 1), ("Read test photo", "Test photo"),
             ("Test photo", "Router request"), ("Router request", "Router"), ("Router", "Route"), ("Route", "Out of scope?"),
             ("Out of scope?", "Refusal", 0), ("Out of scope?", "Vision?", 1), ("Refusal", "Output"),
             ("Vision?", "Vision request", 0), ("Vision?", "Regulations?", 1), ("Vision request", "Vision"), ("Vision", "Vision facts"),
             ("Vision facts", "Regulations?"),
             ("Regulations?", "Retrieval start", 0), ("Regulations?", "Calendar?", 1), ("Retrieval start", "Embed question"),
             ("Embed question", "Qdrant official"), ("Qdrant official", "Qdrant fictitious"), ("Qdrant fictitious", "Regulations request"),
             ("Regulations request", "Regulations"), ("Regulations", "Checks"), ("Checks", "Checks failed?"),
             ("Checks failed?", "Revision request", 0), ("Checks failed?", "Regulations section", 1), ("Revision request", "Revision"),
             ("Revision", "Checks again"), ("Checks again", "Regulations section"), ("Regulations section", "Calendar?"),
             ("Calendar?", "Calendar request", 0), ("Calendar?", "Admin?", 1), ("Calendar request", "Exam lookup"),
             ("Exam lookup", "Calendar section"), ("Calendar section", "Admin?"),
             ("Admin?", "Admin request", 0), ("Admin?", "Output", 1), ("Admin request", "Request lookup"), ("Request lookup", "Admin contact"),
             ("Admin contact", "Contact lookup"), ("Contact lookup", "Admin result"), ("Admin result", "Draft wanted?"),
             ("Draft wanted?", "Draft request", 0), ("Draft wanted?", "Admin section", 1), ("Draft request", "Draft message"),
             ("Draft message", "Admin section"), ("Admin section", "Output")]
    return [{"id": WF3_ID, "name": "03_wf3_assistant", "active": False,
             "settings": {"executionOrder": "v1", "callerPolicy": "workflowsFromSameOwner", "errorWorkflow": WF4_ID},
             "nodes": n, "connections": connections(links), "pinData": {}, "tags": []}]


def connections(links: list[tuple]) -> dict:
    conn = {}
    for l in links:
        src, dst, out = l[0], l[1], (l[2] if len(l) > 2 else 0)
        outs = conn.setdefault(src, {"main": []})["main"]
        while len(outs) <= out:
            outs.append([])
        outs[out].append({"node": dst, "type": "main", "index": 0})
    return conn


# --------------------------------------------------------------------------------------------- entries + WF-4
# HTML, not n8n's default Markdown: Markdown ate the brackets of « [D1-…] » and breaks on a lone « _ » (CF-406)
TG_FIELDS = {"appendAttribution": False, "parse_mode": "HTML"}
NEEDS_ACK = r"""
// « je cherche… » only when there is something to search: not for a greeting or a command (CF-406)
const m = $json.message || {};
const photo = Array.isArray(m.photo) && m.photo.length > 0;
return [{ json: { ...$json, ack: photo || !smallTalk(m.text || m.caption || '') } }];
"""
FRIENDLY = "Désolé, je n'ai pas pu traiter ta question à cause d'un problème technique. Réessaie dans un instant, ou contacte la scolarité (scolarite@esprit.tn)."
RUN_ROW = r"""
// One log row per run (ESA-403): what ran and how long — never the question text, the chat id or a name (NFR-03)
const r = $('Assistant').first().json.response;
const row = { ts: new Date().toISOString(), source: SOURCE, intents: r.route.intents, agents: r.route.agents, checks_pass: r.checks.pass,
              failures: r.checks.failures, revised: r.revised, fallback: r.fallback, timings_s: r.timings_s, mode: r.mode, config: r.config };
return [{ json: { line: JSON.stringify(row) + '\n' } }];
"""
ERR_ROW = r"""
const e = $('Assistant').first().json;
const row = { ts: new Date().toISOString(), source: SOURCE, error: String((e.error && (e.error.message || e.error)) || 'unknown').slice(0, 200) };
return [{ json: { line: JSON.stringify(row) + '\n' } }];
"""
ERR_JSON = r"""
// Contract-valid answer when the assistant failed, so the evaluation counts the failure instead of crashing
const body = $('Test entrance').first().json.body || {};
return [{ json: { response: { test_id: String(body.test_id || ''), reply: FRIENDLY, route: { intents: [], agents: [], missing_fields: [] },
  citations: [], retrieved: [], tool_rows: [], checks: { pass: false, failures: ['error'] }, revised: false, fallback: true,
  timings_s: { total: 0 }, mode: body.mode === 'local' ? 'local' : 'hybrid', config: 'error' } } }];
"""


def log_nodes(wf: str, prefix: str, row_js: str, path: str, x: int, y: int, source: str) -> list:
    return [code(wf, f"{prefix} row", [x, y], f"const SOURCE = {J(source)};\n" + row_js),
            node(wf, f"{prefix} to file", "n8n-nodes-base.convertToFile", 1.1, [x + 220, y],
                 {"operation": "toText", "sourceProperty": "line", "options": {"fileName": path.split("/")[-1]}}),
            node(wf, f"{prefix} append", "n8n-nodes-base.readWriteFile", 1.1, [x + 440, y],
                 {"operation": "write", "fileName": path, "dataPropertyName": "data", "options": {"append": True}})]


def assistant_call(wf: str, x: int, y: int) -> dict:
    n = node(wf, "Assistant", "n8n-nodes-base.executeWorkflow", 1.2, [x, y],
             {"source": "database", "workflowId": {"__rl": True, "mode": "id", "value": WF3_ID}, "mode": "once", "options": {"waitForSubWorkflow": True}})
    n["onError"] = "continueErrorOutput"   # output 1 = the assistant failed → friendly reply + error log
    return n


def telegram_entry():
    """Always published: the only owner of the bot's Telegram webhook. No logic here — it all lives in the core."""
    wf = "wf3tg"
    n = [node(wf, "Telegram", "n8n-nodes-base.telegramTrigger", 1.2, [0, 300], {"updates": ["message"], "additionalFields": {"download": True}},
              webhookId=nid(wf, "tg-hook"), credentials=TG),
         code(wf, "Needs ack?", [220, 300], NEEDS_ACK, [ASSISTANT]),
         iff(wf, "Ack?", [440, 300], "$json.ack"),
         node(wf, "Acknowledge", "n8n-nodes-base.telegram", 1.2, [660, 200],
              {"chatId": "={{ $json.message.chat.id }}", "text": CFG["latency"]["ack_message_fr"], "additionalFields": TG_FIELDS},
              credentials=TG),
         code(wf, "Original update", [880, 300], "return [$('Telegram').first()];   // the assistant needs the update, not the ack result"),
         assistant_call(wf, 1100, 300),
         node(wf, "Send reply", "n8n-nodes-base.telegram", 1.2, [1320, 200],
              {"chatId": "={{ $json.chat }}", "text": "={{ $json.reply_tg }}", "additionalFields": TG_FIELDS}, credentials=TG),
         node(wf, "Friendly error", "n8n-nodes-base.telegram", 1.2, [1320, 420],
              {"chatId": "={{ $('Telegram').first().json.message.chat.id }}", "text": FRIENDLY, "additionalFields": TG_FIELDS},
              credentials=TG)]
    n += log_nodes(wf, "Run", RUN_ROW, "/logs/runs.jsonl", 1540, 200, "telegram")
    n += log_nodes(wf, "Error", ERR_ROW, "/logs/errors.jsonl", 1540, 420, "telegram")
    links = [("Telegram", "Needs ack?"), ("Needs ack?", "Ack?"), ("Ack?", "Acknowledge", 0), ("Ack?", "Original update", 1),
             ("Acknowledge", "Original update"), ("Original update", "Assistant"),
             ("Assistant", "Send reply", 0), ("Assistant", "Friendly error", 1),
             ("Send reply", "Run row"), ("Run row", "Run to file"), ("Run to file", "Run append"),
             ("Friendly error", "Error row"), ("Error row", "Error to file"), ("Error to file", "Error append")]
    return [{"id": "cfWF3Telegram001", "name": "03a_wf3_telegram", "active": False,
             "settings": {"executionOrder": "v1", "errorWorkflow": WF4_ID}, "nodes": n, "connections": connections(links), "pinData": {}, "tags": []}]


def test_entry():
    """Published ONLY during evaluation runs (eval/e2e/CONTRACT.md): n8n is public through ngrok."""
    wf = "wf3test"
    n = [node(wf, "Test entrance", "n8n-nodes-base.webhook", 2.1, [0, 300], {"httpMethod": "POST", "path": "wf3-test", "responseMode": "responseNode", "options": {}},
              webhookId=nid(wf, "test-hook")),
         assistant_call(wf, 220, 300),
         node(wf, "Respond", "n8n-nodes-base.respondToWebhook", 1.1, [440, 200],
              {"respondWith": "json", "responseBody": "={{ JSON.stringify($json.response) }}", "options": {}}),
         code(wf, "Error answer", [440, 420], f"const FRIENDLY = {J(FRIENDLY)};\n" + ERR_JSON),
         node(wf, "Respond error", "n8n-nodes-base.respondToWebhook", 1.1, [660, 420],
              {"respondWith": "json", "responseBody": "={{ JSON.stringify($json.response) }}", "options": {}})]
    n += log_nodes(wf, "Run", RUN_ROW, "/logs/runs.jsonl", 660, 200, "test")
    n += log_nodes(wf, "Error", ERR_ROW, "/logs/errors.jsonl", 880, 420, "test")
    links = [("Test entrance", "Assistant"), ("Assistant", "Respond", 0), ("Assistant", "Error answer", 1),
             ("Respond", "Run row"), ("Run row", "Run to file"), ("Run to file", "Run append"),
             ("Error answer", "Respond error"), ("Respond error", "Error row"), ("Error row", "Error to file"), ("Error to file", "Error append")]
    return [{"id": "cfWF3TestEntry01", "name": "03b_wf3_test", "active": False,
             "settings": {"executionOrder": "v1", "errorWorkflow": WF4_ID}, "nodes": n, "connections": connections(links), "pinData": {}, "tags": []}]


WF4_ROW = r"""
// ESA-403: any unhandled error of WF-3 (or its entries) → one row in /logs/errors.jsonl (no student data)
const x = $input.first().json;
const row = { ts: new Date().toISOString(), source: 'error-workflow', workflow: (x.workflow || {}).name || '',
              node: (x.execution || {}).lastNodeExecuted || '', error: String(((x.execution || {}).error || {}).message || '').slice(0, 200) };
return [{ json: { line: JSON.stringify(row) + '\n' } }];
"""


def wf4_workflow():
    wf = "wf4"
    n = [node(wf, "On error", "n8n-nodes-base.errorTrigger", 1, [0, 300], {})]
    n += [code(wf, "Error row", [220, 300], WF4_ROW),
          node(wf, "Error to file", "n8n-nodes-base.convertToFile", 1.1, [440, 300],
               {"operation": "toText", "sourceProperty": "line", "options": {"fileName": "errors.jsonl"}}),
          node(wf, "Error append", "n8n-nodes-base.readWriteFile", 1.1, [660, 300],
               {"operation": "write", "fileName": "/logs/errors.jsonl", "dataPropertyName": "data", "options": {"append": True}})]
    links = [("On error", "Error row"), ("Error row", "Error to file"), ("Error to file", "Error append")]
    return [{"id": WF4_ID, "name": "04_wf4_errors", "active": False, "settings": {"executionOrder": "v1"}, "nodes": n,
             "connections": connections(links), "pinData": {}, "tags": []}]


def main() -> None:
    for name, wf in (("20_llm_call", llm_workflow()), ("03_wf3_assistant", wf3_workflow()),
                     ("03a_wf3_telegram", telegram_entry()), ("03b_wf3_test", test_entry()), ("04_wf4_errors", wf4_workflow())):
        (W / f"{name}.json").write_text(json.dumps(wf, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"workflows/{name}.json ({len(wf[0]['nodes'])} nodes)")


if __name__ == "__main__":
    main()
