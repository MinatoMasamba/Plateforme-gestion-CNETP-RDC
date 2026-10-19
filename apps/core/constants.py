"""Référentiels partagés (provinces, etc.) pour un filtrage homogène."""

PROVINCES_RDC = [
    ('Kinshasa', 'Kinshasa'),
    ('Kongo-Central', 'Kongo-Central'),
    ('Kwango', 'Kwango'),
    ('Kwilu', 'Kwilu'),
    ('Mai-Ndombe', 'Maï-Ndombe'),
    ('Équateur', 'Équateur'),
    ('Sud-Ubangi', 'Sud-Ubangi'),
    ('Nord-Ubangi', 'Nord-Ubangi'),
    ('Mongala', 'Mongala'),
    ('Tshuapa', 'Tshuapa'),
    ('Tshopo', 'Tshopo'),
    ('Bas-Uele', 'Bas-Uélé'),
    ('Haut-Uele', 'Haut-Uélé'),
    ('Ituri', 'Ituri'),
    ('Nord-Kivu', 'Nord-Kivu'),
    ('Sud-Kivu', 'Sud-Kivu'),
    ('Maniema', 'Maniema'),
    ('Haut-Lomami', 'Haut-Lomami'),
    ('Lualaba', 'Lualaba'),
    ('Tanganyika', 'Tanganyika'),
    ('Haut-Katanga', 'Haut-Katanga'),
    ('Lomami', 'Lomami'),
    ('Sankuru', 'Sankuru'),
    ('Kasaï', 'Kasaï'),
    ('Kasaï-Central', 'Kasaï-Central'),
    ('Kasaï-Oriental', 'Kasaï-Oriental'),
]

HORS_PAYS = ('Pas au pays', 'Pas au pays')

PROVINCE_CHOICES = PROVINCES_RDC + [HORS_PAYS]


def province_choices(current=None):
    """Choix de provinces, en conservant une valeur existante hors référentiel."""
    choices = [('', 'Sélectionnez votre province')] + list(PROVINCE_CHOICES)
    if current:
        value = str(current).strip()
        known = {code for code, _ in choices}
        if value and value not in known:
            choices.insert(1, (value, f'{value} (valeur actuelle)'))
    return choices
