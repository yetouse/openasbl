# OpenASBL — Design Spec : Module Comptabilité

## Contexte

Application de gestion comptable pour petites ASBL belges non assujetties à la TVA, en comptabilité simplifiée.

Premier cas d'usage : le Royal Cercle de Voile de Dave (RCVD), ~300 membres, basé à Dave (vallée de la Meuse).

## Stack technique

- **Backend** : Django (Python)
- **Base de données** : SQLite (fichier unique, backup/migration simple)
- **Frontend** : Templates Django + HTMX
- **Déploiement** : VPS Hostinger, Gunicorn + Nginx, HTTPS obligatoire
- **Fichiers statiques** : WhiteNoise

### Justification

- SQLite : un seul fichier à copier pour backup ou migration de VPS
- Django : ORM solide avec SQLite, auth/admin/forms intégrés, `Decimal` natif pour la comptabilité
- HTMX : interactivité sans framework JS séparé, une seule codebase à maintenir

## Architecture

```
Navigateur → Nginx (HTTPS) → Gunicorn → Django
                                          ├── core
                                          ├── accounts
                                          ├── accounting
                                          ├── reports
                                          └── help
                                                ↓
                                          SQLite (db.sqlite3)
```

### Apps Django

| App | Responsabilité |
|---|---|
| `core` | Configuration ASBL : nom, adresse, n° entreprise BCE, dates d'exercice comptable |
| `accounts` | Authentification, utilisateurs, niveaux de permission |
| `accounting` | Écritures recettes/dépenses, catégories, exercices comptables, justificatifs |
| `reports` | Génération de rapports, exports PDF/Excel/XBRL |
| `help` | Aide contextuelle, assistants pas-à-pas, documentation intégrée |

## Comptabilité

### Régime

- Comptabilité **simplifiée** (petite ASBL)
- **Pas de TVA** — tous les montants sont TTC, aucun champ/calcul TVA
- Exercice comptable configurable (dates début/fin au choix de l'ASBL)

### Modèle de données

#### `Organization` (core)
- Nom de l'ASBL
- Adresse du siège social
- Numéro d'entreprise (BCE)
- Email, téléphone

#### `FiscalYear` (accounting)
- `start_date` — date de début
- `end_date` — date de fin
- `status` — ouvert / clôturé
- `organization` — FK vers Organization

#### `Category` (accounting)
- `name` — nom (ex: "Cotisations", "Entretien péniche")
- `type` — recette ou dépense
- `description` — description optionnelle
- `organization` — FK vers Organization

Catégories pré-remplies adaptées à un club sportif :

**Recettes** : Cotisations membres, Subsides communaux/régionaux, Stages voile, Régates (inscriptions), Buvette/bar, Événements, Dons, Divers recettes

**Dépenses** : Entretien bateaux, Entretien péniche/clubhouse, Assurances, Loyer, Charges (eau/électricité), Matériel nautique, Frais administratifs, Événements, Formation moniteurs, Divers dépenses

#### `Entry` (accounting)
- `date` — date de l'opération
- `amount` — montant (Decimal, TTC)
- `description` — libellé
- `category` — FK vers Category
- `fiscal_year` — FK vers FiscalYear
- `type` — recette / dépense
- `attachment` — fichier justificatif (optionnel, prépare le scan mobile futur)
- `created_by` — FK vers User
- `created_at` — timestamp
- `updated_at` — timestamp

#### `Budget` (accounting)
- `fiscal_year` — FK vers FiscalYear
- `category` — FK vers Category
- `planned_amount` — montant prévu (Decimal)

#### `AssetSnapshot` (accounting)
- `fiscal_year` — FK vers FiscalYear
- `date` — date du relevé
- `cash` — caisse (Decimal)
- `bank` — compte bancaire (Decimal)
- `receivables` — créances (Decimal)
- `debts` — dettes (Decimal)
- `notes` — commentaires

## Permissions

Système flexible basé sur 4 niveaux d'accès, sans rôles nommés figés :

| Niveau | Voir | Créer/Modifier | Valider/Clôturer | Gérer utilisateurs |
|---|---|---|---|---|
| **Lecture** | Écritures, rapports | Non | Non | Non |
| **Gestion** | Tout | Écritures, catégories | Non | Non |
| **Validation** | Tout | Tout | Clôture d'exercice | Non |
| **Admin** | Tout | Tout | Tout | Oui |

Exemple d'attribution au RCVD :
- Trésorier → Admin
- Président, Vice-président → Validation
- Secrétaire → Gestion
- Vérificateurs aux comptes → Lecture

## Rapports et exports

### Rapports obligatoires (légaux)
- **Journal des recettes/dépenses** — toutes les écritures de l'exercice
- **État du patrimoine** — avoirs et dettes à la clôture
- **Comptes annuels** — document à déposer au greffe du tribunal de l'entreprise

### Rapports pratiques
- **Rapport mensuel CA** — résumé pour les réunions mensuelles du conseil d'administration : recettes/dépenses du mois, solde de trésorerie (caisse + banque), comparaison budget prévisionnel vs réalisé, écritures marquantes
- **Suivi budgétaire** — prévisionnel vs réalisé par catégorie
- **Résumé par catégorie** — ventilation des montants par catégorie
- **Historique par exercice** — comparaison entre années

### Formats d'export
- **PDF** — pour AG, greffe, vérificateurs, réunions CA
- **Excel/CSV** — pour retravailler les données
- **XBRL** — pour dépôt à la Banque Nationale de Belgique (si requis)

## UX et accompagnement

### Interface
- Design responsive (utilisable sur mobile pour consultation)
- Français, préparé pour l'internationalisation (i18n Django)
- Formulaires simples, pas de jargon comptable inutile
- Étapes guidées pour les opérations courantes

### Documentation intégrée
- Aide contextuelle dans chaque page (pas de PDF séparé)
- Explications adaptées aux non-comptables

### Mode assistance
- Assistant de première configuration (infos ASBL, exercice, catégories)
- Saisie d'écriture avec suggestions basées sur l'historique
- Clôture d'exercice : checklist étape par étape
- Génération de rapport CA : guidée

## Évolutions futures (hors scope v1)

- Scan de tickets par photo mobile + OCR (Tesseract)
- Langues supplémentaires (NL, DE, EN)
- API REST (Django REST Framework) pour app mobile
- Gestion des membres (cotisations, annuaire)
- Gestion administrative (PV d'AG, registre des membres)
