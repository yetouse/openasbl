from accounting.models import Category, CategoryType

DEFAULT_CATEGORIES = [
    # Recettes
    (CategoryType.INCOME, "Versements membres"),
    (CategoryType.INCOME, "Subsides Namur"),
    (CategoryType.INCOME, "Rentrées consommations"),
    (CategoryType.INCOME, "Manifestations"),
    (CategoryType.INCOME, "Rentrées école voile"),
    (CategoryType.INCOME, "Voile adultes"),
    (CategoryType.INCOME, "Subsides autres (adeps)"),
    (CategoryType.INCOME, "Echos & publicité"),
    (CategoryType.INCOME, "Dons"),
    (CategoryType.INCOME, "Fédération licences"),
    (CategoryType.INCOME, "Carnet de dépôt"),
    # Dépenses
    (CategoryType.EXPENSE, "Assurances"),
    (CategoryType.EXPENSE, "Contrats moniteurs"),
    (CategoryType.EXPENSE, "Elect & eau"),
    (CategoryType.EXPENSE, "Fédération licences"),
    (CategoryType.EXPENSE, "Frais école voile"),
    (CategoryType.EXPENSE, "Gestion admin"),
    (CategoryType.EXPENSE, "Maintenance TT"),
    (CategoryType.EXPENSE, "Régates manif"),
    (CategoryType.EXPENSE, "Repas boissons"),
    (CategoryType.EXPENSE, "Taxes & locations"),
    (CategoryType.EXPENSE, "Travaux entretiens"),
    (CategoryType.EXPENSE, "Voile adultes"),
    (CategoryType.EXPENSE, "Transfert vers carnet dépôt"),
    (CategoryType.EXPENSE, "Echos & publicité"),
]


def seed_categories(organization):
    for category_type, name in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            organization=organization,
            name=name,
            category_type=category_type,
        )
