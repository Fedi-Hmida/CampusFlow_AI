# data/raw — import manifest

Imported 25 Oct 2026 (CF-101) from the team delivery. Files are byte-identical copies (`cp -p`): **never edit them**;
cleaned versions are produced by scripts in `scripts/`. `excluded/` is git-ignored.

Checksums verified: **17/17 identical** (SHA-256 of source and copy).

| Source (Downloads, relative to the delivery folder) | Target | Size (bytes) | SHA-256 | Check | Status | Reason |
|---|---|---|---|---|---|---|
| reglementation/ESPRIT_Guide_des_stages_2024-25.pdf | data/raw/regs/ESPRIT_Guide_des_stages_2024-25.pdf | 4727 | `28dc26d6bbc8becb12639760e08e4885360eea3c662ccf7ab7aaa4994e5f64dd` | OK | kept | synthetic procedure — to be labelled FICTITIOUS (ADR-013) |
| reglementation/ESPRIT_Procedure_Absences_Justificatifs_Rattrapage_2024-25.pdf | data/raw/regs/ESPRIT_Procedure_Absences_Justificatifs_Rattrapage_2024-25.pdf | 6466 | `a60f3f92903e3bbf52baea2454f39f18f4fc76ce8d8e24b01390a53bcecb7e3a` | OK | kept | synthetic procedure — to be labelled FICTITIOUS (ADR-013) |
| reglementation/ESPRIT_Procedure_Amenagements_examens_2024-25.pdf | data/raw/regs/ESPRIT_Procedure_Amenagements_examens_2024-25.pdf | 4416 | `2683c97fa9d194b26e8807170ce0d104500b003c13601b83703334c9b1ead731` | OK | kept | synthetic procedure — to be labelled FICTITIOUS (ADR-013) |
| reglementation/ESPRIT_Procedure_Certificats_Releves_de_notes_2024-25.pdf | data/raw/regs/ESPRIT_Procedure_Certificats_Releves_de_notes_2024-25.pdf | 3516 | `9fc96a0656f9e380e01c6b082a5814b5d3441f4e7cd0b68067ad019e72e288d7` | OK | kept | synthetic procedure — to be labelled FICTITIOUS (ADR-013) |
| reglementation/ESPRIT_Procedure_Depot_Soutenance_PFE_2024-25.pdf | data/raw/regs/ESPRIT_Procedure_Depot_Soutenance_PFE_2024-25.pdf | 4966 | `d8aeedbb9a83fb10fbaf529c59c8bc0f17c5df66b69c3b87132cdff1f0d75853` | OK | kept | synthetic procedure — to be labelled FICTITIOUS (ADR-013) |
| reglementation/ESPRIT_Procedure_Reclamation_Revision_Note_2024-25.pdf | data/raw/regs/ESPRIT_Procedure_Reclamation_Revision_Note_2024-25.pdf | 4765 | `4f0f83cc7d68837d5ad1c6a875bd3d05101e8923838a303a607e24f4af533fab` | OK | kept | synthetic procedure — to be labelled FICTITIOUS (ADR-013) |
| reglementation/ESPRIT_Procedure_Report_Annulation_Inscription_2024-25.pdf | data/raw/regs/ESPRIT_Procedure_Report_Annulation_Inscription_2024-25.pdf | 4364 | `332679a03d877f4344c5ed08e1a32a50ec6ec22ce062ce9ce274069e360b66b6` | OK | kept | synthetic procedure — to be labelled FICTITIOUS (ADR-013) |
| reglementation/ESPRIT_Reglement_interieur_vie_campus_2024-25.pdf | data/raw/regs/ESPRIT_Reglement_interieur_vie_campus_2024-25.pdf | 5324 | `f0f61ff638173902dda53e668acaaa52639ab04f083a6a43fe6d3a8082beb03f` | OK | kept | synthetic procedure — to be labelled FICTITIOUS (ADR-013) |
| reglementation/REGLEMENT-ALT2024-2025.pdf | data/raw/regs/REGLEMENT-ALT2024-2025.pdf | 244200 | `de7733ed245eda131dd774a3b9f1c603a4c6451bba13da3bbdf137d973c6bc56` | OK | kept | real regulation — alternance |
| reglementation/Reglement-scolarite-24-25-cs.pdf | data/raw/regs/Reglement-scolarite-24-25-cs.pdf | 177772 | `d040a651072bbd0a470949dd746a66d202e300336b3a7bacd273b18db0f634e2` | OK | kept | real regulation — cours du soir |
| reglementation/Règlement-de-la-scolarité_cours-du-jour-24-25.pdf | data/raw/regs/Règlement-de-la-scolarité_cours-du-jour-24-25.pdf | 421315 | `d3674e45780fb81dc6209cde50a04f7795d776053b6947dca4bb933b46505913` | OK | kept | real regulation — cours du jour |
| administration contact/D3_annuaire_hierarchie.csv | data/raw/tables/D3_annuaire_hierarchie.csv | 3761 | `53f1882a776851419107bb53aadd0d9f0f3a2f9921509c510c753e90beb68315` | OK | kept | raw table — cleaned by script (ADR-015) |
| request_admin/D4_catalogue_demandes.csv | data/raw/tables/D4_catalogue_demandes.csv | 8266 | `34a38444d58bb3a97c0e43eb959cad594a7427ff0e296af48388a36e27f19616` | OK | kept | raw table — cleaned by script (ADR-015) |
| calendrier/exam_calendar_D2_v4.xlsx | data/raw/tables/exam_calendar_D2_v4.xlsx | 94964 | `4d0828a01ec9faf8eb5f8f0b3f6313b228ee878144bef4da4f924240b2cfecfc` | OK | kept | raw table — cleaned by script (ADR-015) |
| reglementation/Charte-des-examens_étudiants-25.pdf | data/raw/excluded/Charte-des-examens_étudiants-25.pdf | 62127 | `668dede11165debb292cc068c85aa7013120aec9a527cb167e4ef262cdc2f63f` | OK | excluded | 98.8 % of its text is contained in the day regulation (Art. 7-8); indexing it would duplicate chunks. |
| reglementation/Procédure-de-depot.pdf | data/raw/excluded/Procédure-de-depot.pdf | 44558 | `f46fd630f7596f03e622ab51971acc0613a8ac4fa42c0cc2f27132a65b5e4863` | OK | excluded | 2011-2012 PFE deposit procedure (outdated: 4 printed copies + CD-ROM) and contains 2 named staff e-mail addresses (personal data). |
| reglementation/Reglement-de-la-scolarite_cours-du-jour-24-25.pdf | data/raw/excluded/Reglement-de-la-scolarite_cours-du-jour-24-25.pdf | 225108 | `bc554ae6e8328da34289fc7147c87372ddff3921457d46d09f61dcda38097a0c` | OK | excluded | Duplicate of the Word 365 day regulation (8-word shingle Jaccard 0.953); older iLovePDF export (2025-02-25). |
