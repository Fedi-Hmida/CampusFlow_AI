# Lookup tools — live test (CF-019)

Each query is sent to the deployed n8n tool workflow (through the temporary webhook `03t_tools_test`) and to
`workflows/lib/lookup.js` run locally with Node on the same CSV files. **Pass = identical JSON.**
Unit tests of the same code: `node --test workflows/lib/lookup.test.js` (30 tests).

| # | Tool | Query | Status | Result | Live = local |
|---|---|---|---|---|---|
| 1 | exam | `{"module": "Advanced Deep Learning", "class_group": "5DS6", "session": "Principale"}` | found | FX001 | ✅ |
| 2 | exam | `{"module": "ds14", "class_group": "5ds6", "session": "session de contrôle"}` | found | FX010 | ✅ |
| 3 | exam | `{"module": "Financial Analysis", "class_group": "3A1", "session": "Rattrapage"}` | not_published | — | ✅ |
| 4 | exam | `{"module": "Quantum Computing", "class_group": "5DS6"}` | not_found | — | ✅ |
| 5 | exam | `{"module": "DS14"}` | needs_input | class_group | ✅ |
| 6 | contact | `{"role_id": "FIN"}` | found | FIN | ✅ |
| 7 | contact | `{"class_group": "3A12"}` | found | SCO-3A | ✅ |
| 8 | contact | `{"topic": "mobilité internationale"}` | found | MOB | ✅ |
| 9 | contact | `{"role_id": "XYZ"}` | not_found | — | ✅ |
| 10 | contact | `{}` | needs_input | role_id or topic or class_group | ✅ |
| 11 | request | `{"request_id": "REQ-01", "class_group": "4SE1"}` | found | REQ-01 → SCO-4A | ✅ |
| 12 | request | `{"request_id": "REQ-08"}` | needs_input | regime | ✅ |
| 13 | request | `{"request_id": "REQ-08", "regime": "soir"}` | found | REQ-08-SA → SCO-GEN | ✅ |
| 14 | request | `{"topic": "convention de stage", "regime": "jour"}` | found | REQ-14 → STAGE | ✅ |
| 15 | request | `{"request_id": "REQ-14", "regime": "soir"}` | not_applicable | — | ✅ |

**15/15 identical.**
