from accounting.models import Category, CategoryType

DEFAULT_CATEGORIES = [
    (CategoryType.INCOME, "Cotisations membres"),
    (CategoryType.INCOME, "Subsides communaux/régionaux"),
    (CategoryType.INCOME, "Stages voile"),
    (CategoryType.INCOME, "Régates (inscriptions)"),
    (CategoryType.INCOME, "Buvette/bar"),
    (CategoryType.INCOME, "Événements (recettes)"),
    (CategoryType.INCOME, "Dons"),
    (CategoryType.INCOME, "Divers recettes"),
    (CategoryType.EXPENSE, "Entretien bateaux"),
    (CategoryType.EXPENSE, "Entretien péniche/clubhouse"),
    (CategoryType.EXPENSE, "Assurances"),
    (CategoryType.EXPENSE, "Loyer"),
    (CategoryType.EXPENSE, "Charges (eau/électricité)"),
    (CategoryType.EXPENSE, "Matériel nautique"),
    (CategoryType.EXPENSE, "Frais administratifs"),
    (CategoryType.EXPENSE, "Événements (dépenses)"),
    (CategoryType.EXPENSE, "Formation moniteurs"),
    (CategoryType.EXPENSE, "Divers dépenses"),
]


def seed_categories(organization):
    for category_type, name in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            organization=organization,
            name=name,
            defaults={"category_type": category_type},
        )
