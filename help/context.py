HELP_TEXTS = {
    "entry_create": (
        "<strong>Nouvelle écriture comptable</strong><br><br>"
        "Une écriture correspond à une opération financière : une <strong>recette</strong> "
        "(argent qui entre) ou une <strong>dépense</strong> (argent qui sort).<br><br>"
        "<strong>Comment faire :</strong><br>"
        "1. Sélectionnez la <strong>catégorie</strong> correspondante (cotisations, achats, etc.)<br>"
        "2. La date du jour est pré-remplie, modifiez-la si nécessaire<br>"
        "3. Indiquez le <strong>montant TTC</strong> (pas de TVA à gérer pour les ASBL non assujetties)<br>"
        "4. Ajoutez une <strong>description claire</strong> (ex : « Cotisation Jean Dupont 2026 »)<br><br>"
        "<strong>Astuce :</strong> Utilisez le bouton « Enregistrer et nouveau » pour saisir "
        "plusieurs écritures à la suite sans revenir à la liste."
    ),
    "entry_list": (
        "<strong>Journal des écritures</strong><br><br>"
        "Le journal liste toutes les opérations financières de l'exercice en cours. "
        "Les recettes apparaissent en <strong style='color:#16a34a;'>vert</strong>, "
        "les dépenses en <strong style='color:#dc2626;'>rouge</strong>.<br><br>"
        "<strong>Filtres disponibles :</strong><br>"
        "- <strong>Recherche texte</strong> : cherchez dans les descriptions<br>"
        "- <strong>Par catégorie</strong> : filtrez par type d'opération<br>"
        "- <strong>Par type</strong> : recettes uniquement, dépenses uniquement, ou tout<br><br>"
        "Les totaux en bas de page se mettent à jour selon vos filtres."
    ),
    "fiscal_year": (
        "<strong>Exercices comptables</strong><br><br>"
        "Un exercice comptable couvre une période définie, généralement du 1er janvier "
        "au 31 décembre. Toutes les écritures doivent être rattachées à un exercice.<br><br>"
        "<strong>Règles importantes :</strong><br>"
        "- Un seul exercice peut être <strong>ouvert</strong> à la fois<br>"
        "- Les dates de début et fin sont libres (pas forcément l'année civile)<br>"
        "- Le résumé financier affiche les totaux de recettes, dépenses et le solde<br>"
        "- Le nombre d'écritures est indiqué pour chaque exercice"
    ),
    "fiscal_year_close": (
        "<strong>Clôture d'exercice</strong><br><br>"
        "⚠ <strong>La clôture est définitive et irréversible.</strong><br><br>"
        "<strong>Avant de clôturer, vérifiez que :</strong><br>"
        "1. Toutes les écritures de la période sont saisies<br>"
        "2. L'état du patrimoine (caisse, banque, créances, dettes) est à jour<br>"
        "3. Le budget prévisionnel est complet<br>"
        "4. Les rapports PDF ont été vérifiés<br><br>"
        "<strong>Après la clôture :</strong><br>"
        "- Aucune écriture ne pourra être ajoutée, modifiée ou supprimée<br>"
        "- Les comptes annuels doivent être soumis à l'assemblée générale<br>"
        "- Pour les ASBL belges, le dépôt au greffe du tribunal est obligatoire"
    ),
    "category": (
        "<strong>Catégories comptables</strong><br><br>"
        "Les catégories permettent de classer vos opérations en <strong>recettes</strong> "
        "et <strong>dépenses</strong>. Elles structurent vos rapports et votre suivi budgétaire.<br><br>"
        "<strong>Catégories par défaut :</strong><br>"
        "Des catégories adaptées aux clubs sportifs sont fournies (cotisations, subsides, "
        "achats matériel, assurances, etc.).<br><br>"
        "<strong>Personnalisation :</strong><br>"
        "- Ajoutez des catégories propres à votre ASBL<br>"
        "- Chaque catégorie est soit une recette, soit une dépense<br>"
        "- Une catégorie utilisée dans des écritures ne peut pas être supprimée"
    ),
    "budget": (
        "<strong>Budget prévisionnel</strong><br><br>"
        "Le budget vous permet de planifier les recettes et dépenses attendues pour "
        "l'exercice, catégorie par catégorie.<br><br>"
        "<strong>Comment faire :</strong><br>"
        "- Le formulaire en masse permet de saisir tous les montants en une fois<br>"
        "- Le bouton « Copier depuis l'exercice précédent » reprend les montants "
        "du dernier exercice comme base de travail<br>"
        "- Laissez à 0 les catégories sans budget prévu<br><br>"
        "<strong>Suivi :</strong><br>"
        "Le tableau de bord et le rapport de suivi budgétaire comparent ensuite "
        "le prévu au réalisé avec des barres de progression."
    ),
    "budget_tracking": (
        "<strong>Suivi budgétaire</strong><br><br>"
        "Ce tableau compare le <strong>budget prévu</strong> au <strong>réalisé</strong> "
        "pour chaque catégorie de l'exercice en cours.<br><br>"
        "<strong>Lecture des indicateurs :</strong><br>"
        "- <strong>Barre verte</strong> : dans les limites du budget<br>"
        "- <strong>Barre rouge</strong> : dépassement du budget<br>"
        "- <strong>Pourcentage</strong> : taux de réalisation (réalisé / prévu × 100)<br><br>"
        "<strong>Rapports :</strong> Exportez ce suivi en PDF ou Excel pour vos réunions "
        "de conseil d'administration."
    ),
    "asset_snapshot": (
        "<strong>État du patrimoine</strong><br><br>"
        "L'état du patrimoine recense la situation financière de l'ASBL à une date "
        "donnée.<br><br>"
        "<strong>Postes à renseigner :</strong><br>"
        "- <strong>Caisse</strong> : espèces en caisse<br>"
        "- <strong>Banque</strong> : solde du ou des comptes bancaires<br>"
        "- <strong>Créances</strong> : sommes dues à l'ASBL (cotisations impayées, etc.)<br>"
        "- <strong>Dettes</strong> : sommes que l'ASBL doit à des tiers<br><br>"
        "<strong>Obligation légale :</strong> Un relevé est requis à la clôture de chaque "
        "exercice. Il figure dans les comptes annuels à déposer au greffe."
    ),
    "reports": (
        "<strong>Rapports et documents</strong><br><br>"
        "Générez les documents comptables obligatoires et les rapports de gestion.<br><br>"
        "<strong>Documents disponibles :</strong><br>"
        "- <strong>Journal comptable</strong> (PDF, Excel, CSV) : liste chronologique des écritures<br>"
        "- <strong>État du patrimoine</strong> (PDF) : situation financière à une date<br>"
        "- <strong>Comptes annuels</strong> (PDF, Excel) : document légal complet avec "
        "résumé, ventilation, patrimoine et journal<br>"
        "- <strong>Suivi budgétaire</strong> (PDF, Excel) : comparaison budget vs réalisé<br>"
        "- <strong>Rapport mensuel CA</strong> (PDF) : synthèse mensuelle pour le conseil<br>"
        "- <strong>Comparaison par exercice</strong> (PDF) : évolution sur plusieurs années<br><br>"
        "<strong>Astuce :</strong> Les rapports s'ouvrent dans un nouvel onglet pour ne pas "
        "perdre votre navigation."
    ),
    "dashboard": (
        "<strong>Tableau de bord</strong><br><br>"
        "Vue d'ensemble de l'exercice comptable en cours.<br><br>"
        "<strong>Informations affichées :</strong><br>"
        "- <strong>Résumé financier</strong> : total des recettes, dépenses et solde<br>"
        "- <strong>Suivi budgétaire</strong> : barres de progression par catégorie "
        "(prévu vs réalisé)<br>"
        "- <strong>Dernières écritures</strong> : les opérations les plus récentes<br><br>"
        "Cliquez sur les liens pour accéder directement aux sections détaillées."
    ),
    "organization_settings": (
        "<strong>Paramètres de l'organisation</strong><br><br>"
        "Configurez les informations de votre ASBL qui apparaîtront sur les rapports "
        "et documents officiels.<br><br>"
        "<strong>Champs importants :</strong><br>"
        "- <strong>Nom</strong> : dénomination officielle de l'ASBL<br>"
        "- <strong>Numéro d'entreprise</strong> : numéro BCE (format 0xxx.xxx.xxx)<br>"
        "- <strong>Adresse</strong> : siège social<br>"
        "- <strong>Logo</strong> : apparaîtra sur tous les rapports PDF<br><br>"
        "Ces informations figurent dans l'en-tête des comptes annuels."
    ),
    "user_list": (
        "<strong>Gestion des utilisateurs</strong><br><br>"
        "Gérez les accès à l'application selon 4 niveaux de permission :<br><br>"
        "- <strong>Lecture</strong> : consultation uniquement (tableaux, rapports)<br>"
        "- <strong>Gestion</strong> : ajout et modification des écritures et budgets<br>"
        "- <strong>Validation</strong> : gestion + clôture d'exercice<br>"
        "- <strong>Admin</strong> : tous les droits, y compris la gestion des utilisateurs "
        "et les paramètres<br><br>"
        "Chaque niveau inclut les droits des niveaux inférieurs."
    ),
}


def get_help_text(topic):
    return HELP_TEXTS.get(topic, "")
