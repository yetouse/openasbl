---
name: Stack technique et état du projet
description: OpenASBL v1 implémenté - Django + SQLite + HTMX, 67 tests, déployable sur VPS Hostinger
type: project
---

OpenASBL v1 est implémenté et fonctionnel (2026-04-13).

- Stack : Django 5.x, SQLite, HTMX 2.x, WeasyPrint, openpyxl
- 5 apps Django : core, accounts, accounting, reports, help
- 67 tests passent
- Poussé sur GitHub : https://github.com/yetouse/openasbl
- VPS cible : Hostinger
- Venv : /home/yac/openasbl/venv

**Spec :** docs/superpowers/specs/2026-04-13-openasbl-comptabilite-design.md
**Plan :** docs/superpowers/plans/2026-04-13-openasbl-comptabilite.md

**Prochaines étapes possibles :**
- Export XBRL (dépôt BNB)
- Rapport comptes annuels PDF
- Suivi budgétaire et historique par exercice
- Déploiement sur VPS Hostinger
- Scan de tickets (OCR, prévu pour plus tard)
- Gestion des membres (hors scope v1)

**Why:** Savoir où on en est pour reprendre efficacement.
