# Vision prompts v1 → v4 on T4 (CF-208e)

**Setup (26 Oct 2026):** Gemini `gemini-3.5-flash-lite`, temperature 0, JSON mode, through n8n workflow
`00c_vision_eval` (key stays in the n8n credential). 11 T4 images ([T4_photos.csv](../testsets/T4_photos.csv)): 8 photos
by Ines + blurry (T4-09), rotated (T4-10), unrelated (T4-11). Templates: [P-VISION-001](../../prompts/P-VISION-001.md).
Scorer and raw outputs: [vision_prompt_eval.py](vision_prompt_eval.py), `vision_results/<version>/<id>.json`
(re-score offline with `--score-only`). Earlier comparison by Ines (AI Studio, no ground truth):
[vision_v1_v2_comparison.md](vision_v1_v2_comparison.md).

**Scoring:** each expected field of each image (88 in total) is *correct*, *abstained* (null where a value exists),
*wrong* (a different value, or any value where the truth is null = invented) or *not produced* (the version has no
such key). v1 / v2 outputs are mapped onto the v3 vocabulary first (ISO dates, « 09h00 – 11h00 » → start/end,
« Session de contrôle » → Rattrapage, « Devoir surveillé » → DS), so they are not penalised for wording.

## Results
| Metric | v1 | v2 | v3 | v4 |
|---|---:|---:|---:|---:|
| Valid JSON | 11/11 | 11/11 | 11/11 | 11/11 |
| Valid against `vision.schema.json` | — | — | 7/11 | **10/11** |
| Fields correct (of 88) | 71 | 82 | 86 | **87** |
| Wrong values | 4 | 1 | 1 | 1 |
| Abstained | 0 | 0 | 1 | 0 |
| Not produced (no key in that version) | 13 | 5 | 0 | 0 |
| assessment ↔ session confusions | 1 | 0 | 0 | 0 |
| Injection flagged on T4-08 / no false flag elsewhere | cannot express | cannot express | yes / yes | yes / yes |
| Injection text copied into a field | 0 | 0 | 0 | 0 |
| `regime` invented (truth = null on every image) | 0 | 0 | 0 | 0 |
| Hidden room T4-03 left null | yes | yes | yes | yes |
| Timetable entries recovered T4-06 / T4-10 (of 14) | 0 / 0 | 0 / 0 | 14 / 14 | 14 / 13 |
| Mean latency per image | 21.5 s | 21.4 s | 30.2 s | 16.2 s |

## What each version fixed — and what broke
| Version | Failure (input) | Fix | Measured effect |
|---|---|---|---|
| v1 → v2 | v1: `session` = « DS (devoir surveillé) » on T4-03; `class_group` « Classe 2A7 » / « SD56 » (T4-06, T4-10, T4-09 blurry); no way to say DS vs Examen. | v2 adds `type_evaluation`, restricts `regime`. | wrong 4 → 1; correct 71 → 82. |
| v2 → v3 | v2: French keys (schema break); week summarised instead of entries (T4-06, T4-10: 0/14); no injection flag. | English schema keys, `assessment`/`session` enums, `timetable.entries`, `change`, `injection_detected`, `unrelated`. | correct 82 → 86; timetable 0 → 14/14; injection flagged. **New failure:** the template showed `"change": null` / `"timetable": null` without their inner shape → `change` returned as a string (T4-04, T4-05) and `timetable` as a list (T4-06, T4-10): 4 schema violations. |
| v3 → v4 | v3 schema violations above; `class_group` « Classe 2A7 » (T4-10). | Inner shape of `change` and `timetable` written in the template; « values only, no label » rule (class, room, code). | schema-valid 7 → 10/11; correct 86 → 87. **Remaining:** T4-10 (rotated) lists empty cells with `module_name: null` (schema) and recovers 13/14; T4-09 (blurry) reads « 5D56 » instead of abstaining. |

## Honest limits
- **One run per version, 11 images.** Differences of one field (86 vs 87) are within run-to-run noise; the clear
  effects are the keys/schema, the timetable entries, the injection flag and the assessment/session split.
- **Ines's v2 failure did not reproduce here:** in AI Studio she observed `type_evaluation` = « Rattrapage » on 2 images;
  with temperature 0 and JSON mode our v2 run got the field right on all 11. Same model name, different settings.
- Scoring checks the scored fields, not `module_name` free text nor the exact wording of `visible_rules`.
- Ground truth was read from the images by the integration review and still needs Fedi's tick
  ([T4 review sheet](../review/sheets/T4_review.md)).

## Next (v5 candidates, Ines)
1. Rotated timetable: « une entrée par case **remplie** ; ignore les cases vides ».
2. Blurry image: « si un caractère est incertain, mets le champ à null » — the classic abstain-vs-guess trade-off; measure
   on T4-09 plus a second degraded image.
