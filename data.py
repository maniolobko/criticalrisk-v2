SECTORS = {
    "Industrie manufacturiere": {
        "materials": ["Acier", "Aluminium", "Cuivre", "Composants machines"],
        "baseline": 58,
    },
    "Electronique": {
        "materials": ["Semi-conducteurs", "RAM", "PCB", "Terres rares", "Cuivre"],
        "baseline": 72,
    },
    "Automobile": {
        "materials": ["Lithium", "Cobalt", "Nickel", "Semi-conducteurs", "Aluminium"],
        "baseline": 70,
    },
    "Agroalimentaire": {
        "materials": ["Engrais NPK", "Soja", "Ble dur", "Emballages", "Energie"],
        "baseline": 55,
    },
    "Construction": {
        "materials": ["Acier", "Ciment", "Aluminium", "Cuivre", "Bois"],
        "baseline": 50,
    },
    "Textile": {
        "materials": ["Coton", "Polyester", "Colorants", "Fibres recyclees"],
        "baseline": 52,
    },
}

MATERIAL_RISK = {
    "Semi-conducteurs": {"concentration": 88, "volatility": 78, "substitution": 82},
    "RAM": {"concentration": 84, "volatility": 80, "substitution": 76},
    "PCB": {"concentration": 70, "volatility": 58, "substitution": 55},
    "Terres rares": {"concentration": 92, "volatility": 80, "substitution": 86},
    "Lithium": {"concentration": 78, "volatility": 86, "substitution": 74},
    "Cobalt": {"concentration": 90, "volatility": 84, "substitution": 78},
    "Nickel": {"concentration": 68, "volatility": 76, "substitution": 56},
    "Cuivre": {"concentration": 62, "volatility": 72, "substitution": 60},
    "Aluminium": {"concentration": 56, "volatility": 62, "substitution": 42},
    "Acier": {"concentration": 48, "volatility": 58, "substitution": 40},
    "Ciment": {"concentration": 45, "volatility": 50, "substitution": 48},
    "Bois": {"concentration": 44, "volatility": 48, "substitution": 38},
    "Engrais NPK": {"concentration": 76, "volatility": 82, "substitution": 68},
    "Soja": {"concentration": 64, "volatility": 66, "substitution": 52},
    "Ble dur": {"concentration": 58, "volatility": 70, "substitution": 45},
    "Emballages": {"concentration": 42, "volatility": 50, "substitution": 35},
    "Energie": {"concentration": 62, "volatility": 88, "substitution": 58},
    "Coton": {"concentration": 66, "volatility": 60, "substitution": 55},
    "Polyester": {"concentration": 55, "volatility": 58, "substitution": 42},
    "Colorants": {"concentration": 72, "volatility": 64, "substitution": 63},
    "Fibres recyclees": {"concentration": 44, "volatility": 42, "substitution": 35},
    "Composants machines": {"concentration": 64, "volatility": 62, "substitution": 66},
}

SHOCK_SCENARIOS = {
    "Restriction export Asie": {
        "description": "Controle export, quotas ou tension diplomatique sur une zone d'approvisionnement.",
        "affected": ["Semi-conducteurs", "RAM", "PCB", "Terres rares", "Composants machines"],
        "severity": 18,
    },
    "Blocage route maritime": {
        "description": "Hausse des delais et des couts logistiques sur une route critique.",
        "affected": ["Cuivre", "Aluminium", "Soja", "Ble dur", "Coton", "PCB"],
        "severity": 14,
    },
    "Choc energie": {
        "description": "Hausse brutale du cout de l'energie impactant production et transport.",
        "affected": ["Acier", "Aluminium", "Ciment", "Energie", "Engrais NPK"],
        "severity": 16,
    },
}

PERSONAS = [
    "PME industrielle",
    "Direction achats",
    "Direction operations",
    "Importateur / distributeur",
    "Dirigeant non specialiste risque",
]
