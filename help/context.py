HELP_TEXTS = {
    "entry_create": "Une écriture correspond à une opération financière : une recette (argent qui entre) ou une dépense (argent qui sort). Choisissez la catégorie correspondante, indiquez la date, le montant TTC et une description claire. Vous pouvez joindre un justificatif (ticket, facture).",
    "entry_list": "Le journal liste toutes vos écritures. Vous pouvez filtrer par exercice comptable. Les recettes apparaissent en vert, les dépenses en rouge.",
    "fiscal_year": "Un exercice comptable couvre une période définie (souvent une année). Toutes les écritures doivent être rattachées à un exercice. Une fois clôturé, aucune modification n'est possible.",
    "fiscal_year_close": "La clôture d'un exercice est définitive. Avant de clôturer, assurez-vous que toutes les écritures sont saisies et que l'état du patrimoine est à jour. Vous devrez ensuite déposer les comptes annuels au greffe.",
    "category": "Les catégories permettent de classer vos recettes et dépenses. Des catégories par défaut sont fournies, mais vous pouvez en ajouter selon les besoins de votre ASBL.",
    "budget": "Le budget prévisionnel vous permet de planifier les recettes et dépenses par catégorie pour un exercice. Le suivi budgétaire compare ensuite le prévu au réalisé.",
    "asset_snapshot": "L'état du patrimoine recense vos avoirs (caisse, banque, créances) et vos dettes à une date donnée. Il est obligatoire à la clôture de chaque exercice.",
    "reports": "Les rapports vous permettent de générer les documents obligatoires (journal, état du patrimoine, comptes annuels) ainsi que le rapport mensuel pour le conseil d'administration. Disponibles en PDF, Excel et CSV.",
    "dashboard": "Le tableau de bord affiche un résumé de l'exercice en cours : total des recettes, des dépenses, solde et nombre d'écritures.",
}


def get_help_text(topic):
    return HELP_TEXTS.get(topic, "")
