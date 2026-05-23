from dataclasses import dataclass

from data import MATERIAL_RISK, SECTORS, SHOCK_SCENARIOS


@dataclass
class RiskResult:
    global_score: int
    target_score: int
    score_reduction: int
    probability: int
    impact: int
    level: str
    dimensions: dict
    exposure_eur: int
    non_action_cost: int
    residual_cost: int
    estimated_savings: int
    executive_summary: str
    root_causes: list
    data_gaps: list
    mitigation: list
    scenario_impacts: list


def clamp(value, low=0, high=100):
    return max(low, min(high, int(round(value))))


def risk_level(score):
    if score >= 75:
        return "Critique"
    if score >= 55:
        return "Eleve"
    if score >= 35:
        return "Modere"
    return "Faible"


def level_color(score):
    if score >= 75:
        return "#dc2626"
    if score >= 55:
        return "#ea580c"
    if score >= 35:
        return "#d4a041"
    return "#16a34a"


def average(values):
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else 0


def calculate_risk(inputs):
    sector = inputs["sector"]
    materials = inputs["materials"]
    suppliers = inputs["suppliers"]
    single_supplier_share = inputs["single_supplier_share"]
    stock_weeks = inputs["stock_weeks"]
    substitution_months = inputs["substitution_months"]
    annual_spend = inputs["annual_spend"]
    revenue_dependency = inputs["revenue_dependency"]
    risk_maturity = inputs["risk_maturity"]
    contract_coverage = inputs.get("contract_coverage", 35)
    price_hedging = inputs.get("price_hedging", 20)
    logistics_diversity = inputs.get("logistics_diversity", 30)
    monitoring = inputs.get("monitoring", 30)
    incident_history = inputs.get("incident_history", 20)

    sector_baseline = SECTORS[sector]["baseline"]
    material_profiles = [MATERIAL_RISK[m] for m in materials]

    concentration = average([m["concentration"] for m in material_profiles])
    volatility = average([m["volatility"] for m in material_profiles])
    substitutability = average([m["substitution"] for m in material_profiles])

    supplier_risk = 28
    if suppliers <= 1:
        supplier_risk = 92
    elif suppliers == 2:
        supplier_risk = 76
    elif suppliers <= 4:
        supplier_risk = 54

    dependency_risk = single_supplier_share
    stock_risk = clamp(95 - (stock_weeks * 7))
    substitution_risk = clamp(20 + substitution_months * 7)
    maturity_risk = clamp(100 - ((risk_maturity * 0.65) + (monitoring * 0.35)))
    contract_risk_reducer = contract_coverage * 0.18
    hedge_risk_reducer = price_hedging * 0.22
    logistics_risk_reducer = logistics_diversity * 0.18
    incident_penalty = incident_history * 0.16
    revenue_risk = clamp(revenue_dependency)

    dimensions = {
        "Geopolitique": clamp((concentration * 0.7) + (sector_baseline * 0.3)),
        "Supply chain": clamp((supplier_risk * 0.42) + (dependency_risk * 0.32) + (stock_risk * 0.18) - logistics_risk_reducer + incident_penalty),
        "Prix et volatilite": clamp((volatility * 0.62) + (revenue_risk * 0.32) - hedge_risk_reducer - contract_risk_reducer + incident_penalty),
        "Substituabilite": clamp((substitutability * 0.55) + (substitution_risk * 0.45)),
        "Maturite risque": maturity_risk,
    }

    probability = clamp(
        dimensions["Geopolitique"] * 0.30
        + dimensions["Supply chain"] * 0.35
        + dimensions["Prix et volatilite"] * 0.20
        + dimensions["Maturite risque"] * 0.15
    )
    impact = clamp(
        dimensions["Supply chain"] * 0.25
        + dimensions["Prix et volatilite"] * 0.25
        + dimensions["Substituabilite"] * 0.25
        + revenue_risk * 0.25
    )
    global_score = clamp((probability * 0.52) + (impact * 0.48))

    exposure_eur = int(annual_spend * revenue_dependency / 100)
    non_action_cost = int(exposure_eur * (global_score / 100) * 0.55)

    root_causes = build_root_causes(dimensions, inputs, materials)
    mitigation = build_mitigation(dimensions, inputs, global_score, non_action_cost)
    score_reduction = clamp(sum(action["score_effect"] for action in mitigation), 0, 35)
    target_score = clamp(global_score - score_reduction)
    residual_cost = int(exposure_eur * (target_score / 100) * 0.55)
    estimated_savings = max(0, non_action_cost - residual_cost)
    data_gaps = build_data_gaps(inputs, dimensions)
    executive_summary = build_executive_summary(inputs, global_score, target_score, non_action_cost)
    scenario_impacts = build_scenarios(materials, global_score, non_action_cost)

    return RiskResult(
        global_score=global_score,
        target_score=target_score,
        score_reduction=score_reduction,
        probability=probability,
        impact=impact,
        level=risk_level(global_score),
        dimensions=dimensions,
        exposure_eur=exposure_eur,
        non_action_cost=non_action_cost,
        residual_cost=residual_cost,
        estimated_savings=estimated_savings,
        executive_summary=executive_summary,
        root_causes=root_causes,
        data_gaps=data_gaps,
        mitigation=mitigation,
        scenario_impacts=scenario_impacts,
    )


def build_root_causes(dimensions, inputs, materials):
    causes = []
    ranked = sorted(dimensions.items(), key=lambda item: item[1], reverse=True)

    for name, value in ranked[:3]:
        if name == "Supply chain":
            causes.append({
                "title": "Dependance fournisseur concentree",
                "detail": f"{inputs['suppliers']} fournisseur(s) qualifie(s), avec {inputs['single_supplier_share']}% du besoin porte par le principal fournisseur.",
                "severity": value,
            })
        elif name == "Geopolitique":
            causes.append({
                "title": "Exposition geographique et industrielle elevee",
                "detail": f"Les composants/matieres selectionnes ({', '.join(materials)}) sont exposes a des zones ou procedes concentres.",
                "severity": value,
            })
        elif name == "Prix et volatilite":
            causes.append({
                "title": "Volatilite prix et effet marge",
                "detail": f"{inputs['revenue_dependency']}% du chiffre d'affaires depend directement de ces approvisionnements.",
                "severity": value,
            })
        elif name == "Substituabilite":
            causes.append({
                "title": "Substitution lente",
                "detail": f"Le delai estime de substitution ou requalification est de {inputs['substitution_months']} mois.",
                "severity": value,
            })
        elif name == "Maturite risque":
            causes.append({
                "title": "Pilotage risque insuffisant",
                "detail": f"Maturite declaree: {inputs['risk_maturity']}%. La veille, les seuils d'alerte ou les plans de crise semblent incomplets.",
                "severity": value,
            })

    return causes


def build_data_gaps(inputs, dimensions):
    gaps = []
    if dimensions["Supply chain"] >= 55:
        gaps.append("Pays exacts des fournisseurs de rang 1 et 2")
        gaps.append("Delais reels de livraison par fournisseur et route logistique")
    if dimensions["Prix et volatilite"] >= 55:
        gaps.append("Historique prix, volumes achetes et clauses d'indexation")
    if dimensions["Substituabilite"] >= 55:
        gaps.append("Liste des composants substituables et delais de requalification")
    if inputs["risk_maturity"] < 50:
        gaps.append("Responsable interne, seuils d'alerte et protocole de decision")
    return gaps[:6]


def build_executive_summary(inputs, score, target_score, non_action_cost):
    if score >= 75:
        tone = "La situation doit etre traitee comme un risque de continuite d'activite."
    elif score >= 55:
        tone = "La situation justifie un plan de reduction du risque a court terme."
    elif score >= 35:
        tone = "Le risque est contenu mais merite une surveillance structuree."
    else:
        tone = "Le risque actuel parait limite, sous reserve de maintenir une veille active."

    return (
        f"{tone} Pour le profil {inputs['persona']}, le score peut passer de "
        f"{score}/100 a environ {target_score}/100 si les actions prioritaires sont mises en oeuvre. "
        f"Le cout potentiel de non-action est estime a {non_action_cost:,} EUR."
    ).replace(",", " ")


def build_mitigation(dimensions, inputs, score, non_action_cost):
    actions = []

    if dimensions["Supply chain"] >= 55:
        actions.append({
            "horizon": "30 jours",
            "priority": "Priorite 1",
            "title": "Cartographier les fournisseurs critiques",
            "detail": "Identifier les fournisseurs de rang 1 et 2, leur pays d'exposition, les routes logistiques et les alternatives disponibles.",
            "kpi": "100% des fournisseurs critiques qualifies",
            "effort": "Moyen",
            "impact": "Fort",
            "score_effect": 6,
            "value_eur": int(non_action_cost * 0.12),
        })
        actions.append({
            "horizon": "60 jours",
            "priority": "Priorite 2",
            "title": "Qualifier au moins deux sources alternatives",
            "detail": "Lancer une consultation fournisseurs en zone geographique differente pour reduire le risque de fournisseur unique.",
            "kpi": "2 fournisseurs alternatifs qualifies",
            "effort": "Fort",
            "impact": "Fort",
            "score_effect": 9,
            "value_eur": int(non_action_cost * 0.20),
        })

    if dimensions["Substituabilite"] >= 55:
        actions.append({
            "horizon": "90 jours",
            "priority": "Priorite 3",
            "title": "Lancer un plan de substitution technique",
            "detail": "Evaluer les composants ou matieres substituables, les delais de requalification et les impacts certification.",
            "kpi": "1 scenario de substitution teste",
            "effort": "Fort",
            "impact": "Moyen",
            "score_effect": 7,
            "value_eur": int(non_action_cost * 0.14),
        })

    if inputs["stock_weeks"] < 8:
        actions.append({
            "horizon": "30 jours",
            "priority": "Quick win",
            "title": "Recalculer le stock tampon",
            "detail": "Comparer le cout d'un stock additionnel avec le cout d'une rupture de production ou de livraison.",
            "kpi": "Stock tampon cible defini",
            "effort": "Faible",
            "impact": "Moyen",
            "score_effect": 5,
            "value_eur": int(non_action_cost * 0.10),
        })

    if dimensions["Maturite risque"] >= 55:
        actions.append({
            "horizon": "60 jours",
            "priority": "Gouvernance",
            "title": "Mettre en place une revue risque achats mensuelle",
            "detail": "Suivre prix, delais, tensions geopolitiques, alertes fournisseurs et decisions de mitigation.",
            "kpi": "Tableau de bord mensuel actif",
            "effort": "Faible",
            "impact": "Moyen",
            "score_effect": 5,
            "value_eur": int(non_action_cost * 0.08),
        })

    if score < 45:
        actions.append({
            "horizon": "90 jours",
            "priority": "Maintien",
            "title": "Maintenir la veille et tester un scenario de crise",
            "detail": "Votre exposition est contenue, mais une simulation trimestrielle permet d'eviter l'aveuglement.",
            "kpi": "1 exercice de crise realise",
            "effort": "Faible",
            "impact": "Faible",
            "score_effect": 3,
            "value_eur": int(non_action_cost * 0.05),
        })

    return sorted(actions[:6], key=lambda action: (-action["score_effect"], action["horizon"]))


def build_scenarios(materials, score, non_action_cost):
    scenarios = []
    for name, scenario in SHOCK_SCENARIOS.items():
        overlap = len(set(materials).intersection(scenario["affected"]))
        if overlap == 0:
            impact = clamp(score * 0.55)
        else:
            impact = clamp(score + scenario["severity"] + overlap * 4)
        scenarios.append({
            "name": name,
            "description": scenario["description"],
            "impact_score": impact,
            "estimated_cost": int(non_action_cost * (impact / max(score, 1))),
        })
    return sorted(scenarios, key=lambda item: item["impact_score"], reverse=True)
