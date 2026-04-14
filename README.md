<p align="center">
  <img src="static/img/logo-openasbl.png" alt="OpenASBL" width="200">
</p>

<h1 align="center">OpenASBL</h1>

<p align="center">Comptabilité simplifiée pour les petites ASBL belges non assujetties à la TVA.</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue" alt="Python">
  <img src="https://img.shields.io/badge/Django-5.x-green" alt="Django">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

## Présentation

OpenASBL est une application web de comptabilité conçue pour les petites associations sans but lucratif (ASBL) belges. Elle permet de tenir une comptabilité simplifiée conforme aux obligations légales, sans nécessiter de connaissances comptables avancées.

Développée initialement pour le [Royal Cercle de Voile de Dave](https://www.royal-cercle-de-voile-de-dave.be/) (RCVD), l'application est générique et peut être utilisée par toute petite ASBL.

## Fonctionnalités

### Comptabilité
- **Écritures comptables** — Saisie des recettes et dépenses avec catégories, recherche et filtrage avancé
- **Exercices comptables** — Gestion des périodes avec ouverture, clôture et résumé financier
- **Catégories** — Classification des opérations (personnalisables par ASBL)
- **Budget prévisionnel** — Planification par catégorie avec saisie en masse et copie depuis l'exercice précédent
- **Suivi budgétaire** — Comparaison budget vs réalisé avec barres de progression
- **État du patrimoine** — Relevé des actifs (caisse, banque, créances) et passifs (dettes)

### Rapports
- **Journal comptable** (PDF, Excel, CSV)
- **Comptes annuels** (PDF, Excel) — Document légal avec résumé, ventilation, patrimoine et journal
- **Export XBRL (BNB)** — Fichier XBRL pour dépôt électronique à la Banque Nationale de Belgique (modèle micro m08)
- **Suivi budgétaire** (PDF, Excel) — Budget vs réalisé par catégorie
- **Rapport mensuel CA** (PDF) — Synthèse pour le conseil d'administration
- **Comparaison par exercice** (PDF) — Évolution sur plusieurs années
- **État du patrimoine** (PDF)

### Interface
- **Tableau de bord** — Vue d'ensemble avec résumé financier, suivi budgétaire et dernières écritures
- **Aide contextuelle** — Bouton d'aide (?) sur chaque page avec explications détaillées
- **Logo personnalisable** — Upload du logo de l'ASBL (affiché dans la navbar et les rapports PDF)
- **Interface en français** — Préparée pour l'internationalisation (i18n)
- **Responsive** — Utilisable sur mobile et tablette

### Sécurité
- **4 niveaux de permission** : Lecture < Gestion < Validation < Admin
- **Assistant de configuration** — Premier lancement guidé (création ASBL + compte admin)

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Python 3.12+, Django 5.x |
| Base de données | SQLite |
| Frontend | Django Templates, HTMX 2.x, Bootstrap 5.3 |
| PDF | WeasyPrint |
| Excel | openpyxl |
| Fichiers statiques | WhiteNoise |
| Déploiement | Gunicorn + Nginx |

## Installation

### Prérequis

- Python 3.12+
- pip

### Mise en place

```bash
git clone https://github.com/yetouse/openasbl.git
cd openasbl
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Au premier lancement, l'assistant de configuration vous guide pour créer votre ASBL et le compte administrateur.

### Données de démonstration

```bash
# Catégories par défaut (clubs sportifs)
python manage.py seed_categories

# Données de démonstration (exercices, budgets, écritures)
# python manage.py seed_demo_data  # à venir
```

## Tests

```bash
python manage.py test                    # tous les tests (164)
python manage.py test accounting         # tests du module comptabilité
python manage.py test accounting.tests.test_models  # un module spécifique
```

## Déploiement

Les fichiers de configuration pour un déploiement en production sont dans `deploy/` :

- `gunicorn.conf.py` — Configuration Gunicorn (2 workers, timeout 120s pour WeasyPrint)
- `nginx-openasbl.conf` — Reverse proxy Nginx
- `openasbl.service` — Service systemd
- `setup.sh` — Script d'installation serveur

## Architecture

```
openasbl/
├── core/          # Organisation, setup wizard, paramètres
├── accounts/      # Utilisateurs, permissions (4 niveaux), login
├── accounting/    # Exercices, catégories, écritures, budgets, patrimoine
├── reports/       # Générateurs PDF (WeasyPrint), Excel (openpyxl), CSV
├── help/          # Aide contextuelle HTMX
├── templates/     # Templates globaux (base, navbar, footer)
├── static/        # CSS, JS (HTMX), images (logos)
└── deploy/        # Fichiers de déploiement production
```

## Licence

MIT

## Remerciements

