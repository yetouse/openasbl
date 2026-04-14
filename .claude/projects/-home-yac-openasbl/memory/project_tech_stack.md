---
name: Stack technique et état du projet
description: OpenASBL v2 en cours - Django + SQLite + HTMX, 92 tests, données RCVD seedées
type: project
---

OpenASBL v2 en développement (2026-04-14).

- Stack : Django 5.x, SQLite, HTMX 2.x, WeasyPrint, openpyxl, Bootstrap 5.3.3
- 5 apps Django : core, accounts, accounting, reports, help
- 92 tests passent
- Poussé sur GitHub : https://github.com/yetouse/openasbl
- VPS cible : Hostinger (fichier hostinger.json avec MCP config)
- Venv : /home/yac/openasbl/venv

**Spec :** docs/superpowers/specs/2026-04-13-openasbl-comptabilite-design.md
**Plan :** docs/superpowers/plans/2026-04-13-openasbl-comptabilite.md

**Fonctionnalités v2 ajoutées (2026-04-14) :**
- Suivi budgétaire (HTML + PDF + Excel) avec barres de progression
- Comptes annuels PDF + Excel (obligation légale)
- Comparaison par exercice (PDF)
- Dashboard amélioré (budget progress, dernières écritures)
- Formulaire budget en masse (toutes catégories d'un coup)
- Copie budget depuis exercice précédent
- Recherche/filtrage avancé des écritures
- Résumé financier sur la liste des exercices
- Formulaire d'écriture amélioré (date auto, enregistrer et nouveau)
- Seed données réelles RCVD (budget 2026, écritures Q1 2026, patrimoine)
- Category unique_together inclut maintenant category_type

**Prochaines étapes possibles :**
- Déploiement sur VPS Hostinger
- Export XBRL (dépôt BNB)
- Scan de tickets (OCR)
- Gestion des membres (hors scope v1)

**Why:** Savoir où on en est pour reprendre efficacement.
