Zagros AI Structural Firm
An experimental "one-person company" for structural engineering, in which a licensed engineer supervises a team of specialized AI agents that model, analyse, check and document reinforced-concrete and steel buildings.
Why
Small engineering offices repeat the same workflow on every project: load calculation, modelling, analysis, code checks, drawings, calculation report. This project explores how far that workflow can be delegated to AI agents while keeping engineering judgement and responsibility with the engineer.
Architecture
• Head engineer (human): final decisions and sign-off.
• Deputy agent: receives instructions, assigns tasks, collects results, reports.
• Discipline agents: structural (ACI 318-19 / AISC 360-16), seismic & geotechnical (Iranian Standard 2800, 4th ed.), architecture (always three facade options), electrical, gas, mechanical/plumbing, BIM, calculation-report writer, QA/coordination checker.
• Software-operator agents: ETABS 19, SAFE, AutoCAD, FreeCAD, Office – each controlled through its API or scripting interface using Python.
Governance
• COMPANY.md defines the organisation chart and authority limits.
• Each project has a board.md task board and a coordination.md cross-discipline log.
• Main model files are never modified without the head engineer's approval.
• Nothing is labelled "final" without sign-off.
• A scheduled daily email report lists pending decisions first.
Design basis
Concrete: ACI 318-19 · Steel: AISC 360-16 · Loads: ASCE 7-22 · Seismic: Iranian Standard 2800 (4th edition)
Repository contents
• agents/ – agent definition files (roles, responsibilities, code basis, rules)
• scripts/ – Python scripts for ETABS geometry export, section assignment, ACI 318-19 checks, ETABS-to-FreeCAD export, AutoCAD plan generation
• templates/ – project template (CLAUDE.md, board.md, coordination.md)
• docs/ – workflow description and sample (anonymised) outputs
No client data, site information or project model files are included. Sample outputs are anonymised.
Status
Applied to one real project, Merage3, a multi-storey reinforced-concrete residential building in Minoodasht, Golestan Province, Iran (seismic coefficient, base shear, member sizing, column drawing generation). Active development.
Author
Rahmatollah Shirzaei – Structural Engineer (مهندس محاسب), founder of Ahan Beton Zagros.
License
MIT
