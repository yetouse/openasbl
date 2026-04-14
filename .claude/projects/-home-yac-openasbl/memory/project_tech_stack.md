---
name: Stack technique et état du projet
description: OpenASBL v2 déployé - Django + SQLite + HTMX, 92 tests, yetouse.cloud
type: project
---

OpenASBL v2 déployé en production (2026-04-14).

- Stack : Django 5.x, SQLite, HTMX 2.x, WeasyPrint, openpyxl, Bootstrap 5.3.3
- 5 apps Django : core, accounts, accounting, reports, help
- 92 tests passent
- GitHub : https://github.com/yetouse/openasbl
- Production : https://yetouse.cloud (VPS Hostinger)
- Venv local : /home/yac/openasbl/venv

**Spec :** docs/superpowers/specs/2026-04-13-openasbl-comptabilite-design.md
**Plan :** docs/superpowers/plans/2026-04-13-openasbl-comptabilite.md

**Fonctionnalités v2 (2026-04-14) :**
- Suivi budgétaire (HTML + PDF + Excel) avec barres de progression
- Comptes annuels PDF + Excel (obligation légale ASBL)
- Comparaison par exercice (PDF)
- Dashboard amélioré (budget progress, dernières écritures)
- Formulaire budget en masse + copie depuis exercice précédent
- Recherche/filtrage avancé des écritures (texte, catégorie, type)
- Résumé financier sur la liste des exercices
- Formulaire d'écriture amélioré (date auto, enregistrer et nouveau)
- Filtre template |money pour formatage montants (1 234,56)
- Logos (OpenASBL navbar + RCVD dans PDF)
- Rapports s'ouvrent dans nouvel onglet
- Seed données réelles RCVD (seed_rcvd_data)
- Fichiers deploy (Gunicorn, Nginx, systemd, setup.sh)

**Prochaines étapes possibles :**
- Export XBRL (dépôt BNB)
- Scan de tickets (OCR)
- Gestion des membres (hors scope v1)
- Formatage montants dans les PDF (filtre |money pas encore appliqué aux templates PDF)

**Why:** Savoir où on en est pour reprendre efficacement.
