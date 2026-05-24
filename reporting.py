from datetime import date
import html
import io


def money(value):
    return f"{int(value):,}".replace(",", " ") + " EUR"


def confidence_level(result):
    gaps = len(result.data_gaps)
    if gaps >= 5:
        return "Moyen - donnees critiques a consolider"
    if gaps >= 2:
        return "Bon - quelques hypotheses a confirmer"
    return "Eleve - diagnostic suffisamment documente"


def decision_recommendation(result):
    if result.global_score >= 75:
        return "Decision recommandee: lancer un plan de mitigation prioritaire sous 30 jours."
    if result.global_score >= 55:
        return "Decision recommandee: engager un plan de reduction du risque et suivre les indicateurs mensuellement."
    if result.global_score >= 35:
        return "Decision recommandee: maintenir la surveillance et preparer des options alternatives."
    return "Decision recommandee: conserver une veille active et formaliser les seuils d'alerte."


def risk_level_text(score):
    if score >= 75:
        return "Critique"
    if score >= 55:
        return "Eleve"
    if score >= 35:
        return "Modere"
    return "Faible"


def truncate(text, max_len):
    text = str(text)
    return text if len(text) <= max_len else text[: max_len - 1] + "."


def strategic_diagnosis(inputs, result):
    main_dimensions = sorted(result.dimensions.items(), key=lambda item: item[1], reverse=True)[:2]
    leaders = " et ".join(f"{name.lower()} ({score}/100)" for name, score in main_dimensions)
    return (
        f"Le diagnostic montre une exposition prioritaire sur {leaders}. "
        f"Pour un profil {inputs.get('trade_profile', 'import-export')}, cela signifie que le risque ne se limite pas a une rupture ponctuelle: "
        "il peut affecter la continuite commerciale, les marges, les delais clients et la capacite a tenir les engagements contractuels. "
        f"Le score actuel de {result.global_score}/100 doit donc etre lu comme un signal de pilotage: il indique le niveau d'urgence, "
        "mais aussi les leviers concrets permettant de ramener le risque vers un niveau cible plus acceptable."
    )


def financial_diagnosis(result):
    return (
        f"L'exposition economique estimee atteint {money(result.exposure_eur)}. "
        f"En l'absence d'action, le cout potentiel est estime a {money(result.non_action_cost)}, contre un cout residuel de "
        f"{money(result.residual_cost)} apres mise en oeuvre du plan de mitigation. "
        f"L'ecart, soit {money(result.estimated_savings)}, represente la valeur indicative du plan d'action. "
        "Cette estimation doit etre consideree comme un ordre de grandeur decisionnel: elle sert a prioriser les actions et a justifier "
        "l'investissement dans la resilience import-export."
    )


def cause_explanation(cause):
    return (
        f"{cause['title']} est une cause prioritaire car elle pese a {cause['severity']}/100 dans le diagnostic. "
        f"{cause['detail']} Cette faiblesse peut amplifier un choc externe: hausse de prix, retard logistique, blocage douanier, "
        "restriction pays ou perte de capacite fournisseur/client. Le point important n'est pas seulement le niveau du score, mais la capacite "
        "de l'entreprise a reduire cette dependance par des alternatives, de la visibilite et des procedures de decision rapides."
    )


def action_explanation(action):
    return (
        f"{action['title']} doit etre traite sur un horizon {action['horizon'].lower()} car l'action peut reduire le score d'environ "
        f"{action['score_effect']} points. L'objectif operationnel est clair: {action['detail']} "
        f"Le KPI de suivi est: {action['kpi']}. L'effort est estime {action['effort'].lower()} pour un impact {action['impact'].lower()}, "
        f"avec une valeur indicative de {money(action['value_eur'])}."
    )


def build_text_report(company, inputs, result):
    lines = [
        "CRITICALRISK INTELLIGENCE",
        "Rapport de diagnostic import-export",
        f"Date: {date.today().strftime('%d/%m/%Y')}",
        "",
        "1. Synthese decisionnelle",
        f"Entreprise: {company or 'Non renseignee'}",
        f"Profil international: {inputs.get('trade_profile', 'Non renseigne')}",
        f"Secteur: {inputs['sector']}",
        f"Flux critiques: {', '.join(inputs['materials'])}",
        f"Score actuel: {result.global_score}/100 ({result.level})",
        f"Score cible: {result.target_score}/100",
        f"Gain potentiel estime: {money(result.estimated_savings)}",
        decision_recommendation(result),
        "",
        result.executive_summary,
        "",
        "2. Indicateurs financiers",
        f"Exposition economique estimee: {money(result.exposure_eur)}",
        f"Cout potentiel de non-action: {money(result.non_action_cost)}",
        f"Cout residuel apres actions: {money(result.residual_cost)}",
        f"Niveau de confiance: {confidence_level(result)}",
        "",
        "3. Dimensions de risque",
    ]

    for name, score in result.dimensions.items():
        lines.append(f"- {name}: {score}/100")

    lines.extend(["", "4. Causes racines prioritaires"])
    for cause in result.root_causes:
        lines.append(f"- {cause['title']} ({cause['severity']}/100): {cause['detail']}")

    lines.extend(["", "5. Plan d'action priorise"])
    for action in result.mitigation:
        lines.append(
            f"- [{action['horizon']}] {action['priority']} - {action['title']} | "
            f"{action['detail']} KPI: {action['kpi']} | Effort: {action['effort']} | "
            f"Impact: {action['impact']} | Effet score: -{action['score_effect']} pts | "
            f"Valeur estimee: {money(action['value_eur'])}"
        )

    lines.extend(["", "6. Scenarios de stress"])
    for scenario in result.scenario_impacts:
        lines.append(
            f"- {scenario['name']}: impact {scenario['impact_score']}/100, "
            f"cout estime {money(scenario['estimated_cost'])}. {scenario['description']}"
        )

    if result.data_gaps:
        lines.extend(["", "7. Donnees a consolider"])
        for gap in result.data_gaps:
            lines.append(f"- {gap}")

    lines.extend([
        "",
        "8. Methodologie et limites",
        "Le score combine exposition import-export, logistique, reglementaire, prix/devise et resilience interne.",
        "Les resultats constituent une aide a la decision et doivent etre consolides avec donnees fournisseurs, pays, contrats, volumes et historiques reels.",
    ])

    return "\n".join(lines)


def build_pdf(company, inputs, result):
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            BaseDocTemplate,
            Frame,
            PageBreak,
            PageTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            KeepTogether,
            Flowable,
        )
    except ImportError:
        return None

    def clean(text):
        return str(text).replace("’", "'").replace("–", "-").replace("—", "-")

    def esc(text):
        return html.escape(clean(text))

    def color_for_score(score):
        if score >= 75:
            return colors.HexColor("#dc2626")
        if score >= 55:
            return colors.HexColor("#ea580c")
        if score >= 35:
            return colors.HexColor("#d4a041")
        return colors.HexColor("#16a34a")

    class RiskBars(Flowable):
        def __init__(self, dimensions, width=16.2 * cm, height=6.0 * cm):
            super().__init__()
            self.dimensions = list(dimensions.items())
            self.width = width
            self.height = height

        def draw(self):
            c = self.canv
            c.setStrokeColor(colors.HexColor("#dce3ee"))
            c.setFillColor(colors.HexColor("#f8fafc"))
            c.rect(0, 0, self.width, self.height, stroke=1, fill=1)
            c.setFillColor(colors.HexColor("#0b1220"))
            c.setFont("Helvetica-Bold", 9)
            c.drawString(10, self.height - 16, "Graphique des dimensions de risque")
            y = self.height - 35
            label_w = 105
            bar_w = self.width - label_w - 50
            for name, score in self.dimensions:
                c.setFont("Helvetica", 7.2)
                c.setFillColor(colors.HexColor("#334155"))
                c.drawString(10, y, clean(name)[:28])
                c.setFillColor(colors.HexColor("#e5eaf2"))
                c.rect(label_w, y - 1, bar_w, 6, stroke=0, fill=1)
                c.setFillColor(color_for_score(score))
                c.rect(label_w, y - 1, bar_w * score / 100, 6, stroke=0, fill=1)
                c.setFillColor(colors.HexColor("#0b1220"))
                c.setFont("Helvetica-Bold", 7.2)
                c.drawRightString(self.width - 10, y, f"{score}/100")
                y -= 18

    class RiskMatrix(Flowable):
        def __init__(self, probability, impact, score, width=7.0 * cm, height=6.4 * cm):
            super().__init__()
            self.probability = probability
            self.impact = impact
            self.score = score
            self.width = width
            self.height = height

        def draw(self):
            c = self.canv
            size = 4.8 * cm
            x = (self.width - size) / 2
            y = 16
            c.setFillColor(colors.HexColor("#0b1220"))
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(self.width / 2, self.height - 12, "Matrice probabilite / impact")
            labels = [
                ("Faible", "#e3f4ea"), ("Modere", "#fff6d8"), ("Eleve", "#ffeadb"),
                ("Modere", "#fff6d8"), ("Eleve", "#ffeadb"), ("Critique", "#ffe0e0"),
                ("Eleve", "#ffeadb"), ("Critique", "#ffe0e0"), ("Critique", "#ffe0e0"),
            ]
            cell = size / 3
            idx = 0
            for row in range(3):
                for col in range(3):
                    label, fill = labels[idx]
                    c.setFillColor(colors.HexColor(fill))
                    c.setStrokeColor(colors.HexColor("#dce3ee"))
                    c.rect(x + col * cell, y + (2 - row) * cell, cell, cell, stroke=1, fill=1)
                    c.setFillColor(colors.HexColor("#64748b"))
                    c.setFont("Helvetica", 6)
                    c.drawString(x + col * cell + 4, y + (2 - row) * cell + cell - 10, label)
                    idx += 1
            px = x + (self.probability / 100) * size
            py = y + (self.impact / 100) * size
            c.setFillColor(color_for_score(self.score))
            c.circle(px, py, 4, stroke=0, fill=1)
            c.setFillColor(colors.HexColor("#0b1220"))
            c.setFont("Helvetica", 6)
            c.drawCentredString(x + size / 2, y - 10, "Probabilite")
            c.saveState()
            c.translate(x - 12, y + size / 2)
            c.rotate(90)
            c.drawCentredString(0, 0, "Impact")
            c.restoreState()

    buffer = io.BytesIO()
    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")

    def footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawCentredString(A4[0] / 2, 0.8 * cm, f"CriticalRisk Intelligence | Rapport confidentiel | Page {doc_obj.page}")
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="report", frames=[frame], onPage=footer)])

    base = getSampleStyleSheet()
    styles = {
        "cover_label": ParagraphStyle("cover_label", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor("#f5b942"), leading=12),
        "title": ParagraphStyle("title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=25, textColor=colors.white, leading=29, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], fontSize=10.5, textColor=colors.white, leading=14),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=15, textColor=colors.HexColor("#0b1220"), leading=18, spaceBefore=8, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12, textColor=colors.HexColor("#0b1220"), leading=15, spaceBefore=8, spaceAfter=5),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontSize=9.2, leading=13.4, textColor=colors.HexColor("#1f2937"), alignment=TA_LEFT, spaceAfter=7),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontSize=8, leading=11, textColor=colors.HexColor("#475569"), spaceAfter=5),
        "caption": ParagraphStyle("caption", parent=base["BodyText"], fontSize=7.2, leading=9.5, textColor=colors.HexColor("#64748b"), spaceAfter=4),
        "kpi_label": ParagraphStyle("kpi_label", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=7, textColor=colors.HexColor("#64748b"), leading=9),
        "kpi_value": ParagraphStyle("kpi_value", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=12, leading=15),
        "table": ParagraphStyle("table", parent=base["BodyText"], fontSize=7.6, leading=9.5, textColor=colors.HexColor("#1f2937")),
        "table_head": ParagraphStyle("table_head", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=7.4, leading=9, textColor=colors.white, alignment=TA_CENTER),
    }

    def p(text, style="body"):
        return Paragraph(esc(text), styles[style])

    def heading(text, level=1):
        return Paragraph(esc(text), styles["h1" if level == 1 else "h2"])

    def table(headers, rows, widths):
        data = [[Paragraph(esc(h), styles["table_head"]) for h in headers]]
        for row in rows:
            data.append([Paragraph(esc(cell), styles["table"]) for cell in row])
        t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b1220")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dce3ee")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    def kpi_cell(label, value, subtitle, text_color):
        return [
            Paragraph(esc(label), styles["kpi_label"]),
            Paragraph(f'<font color="{text_color}">{esc(value)}</font>', styles["kpi_value"]),
            Paragraph(esc(subtitle), styles["caption"]),
        ]

    story = []
    cover = Table(
        [
            [Paragraph("CRITICALRISK INTELLIGENCE", styles["cover_label"])],
            [Paragraph("Rapport de diagnostic import-export", styles["title"])],
            [Paragraph("Analyse des risques, cout de non-action et plan de mitigation priorise", styles["subtitle"])],
        ],
        colWidths=[doc.width],
        rowHeights=[0.65 * cm, 1.15 * cm, 0.65 * cm],
    )
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#07101d")),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([cover, Spacer(1, 0.45 * cm)])

    kpis = Table([[
        kpi_cell("SCORE ACTUEL", f"{result.global_score}/100", result.level, "#d4a041" if result.global_score < 55 else "#ea580c"),
        kpi_cell("SCORE CIBLE", f"{result.target_score}/100", f"-{result.score_reduction} pts", "#16a34a"),
        kpi_cell("COUT NON-ACTION", money(result.non_action_cost), "estimation", "#dc2626"),
        kpi_cell("GAIN POTENTIEL", money(result.estimated_savings), "apres actions", "#16a34a"),
    ]], colWidths=[doc.width / 4 - 5] * 4)
    kpis.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dce3ee")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dce3ee")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([kpis, Spacer(1, 0.25 * cm)])

    story.extend([
        heading("1. Synthese decisionnelle"),
        p(decision_recommendation(result)),
        p(strategic_diagnosis(inputs, result)),
        p(
            "Ce rapport doit etre lu comme une note de decision. Il identifie les principaux points de fragilite, "
            "quantifie l'ordre de grandeur financier et transforme le diagnostic en actions operationnelles. "
            "Les scores ne remplacent pas un audit exhaustif, mais ils donnent une base structuree pour arbitrer les priorites.",
        ),
        heading("2. Profil analyse", 2),
        table(
            ["Indicateur", "Valeur", "Lecture"],
            [
                ["Entreprise", company or "Non renseignee", "Perimetre de lecture du rapport"],
                ["Profil international", inputs.get("trade_profile", "Non renseigne"), "Nature principale des flux exposes"],
                ["Secteur", inputs["sector"], "Base de risque sectoriel"],
                ["Flux critiques", ", ".join(inputs["materials"]), "Composants ou matieres sensibles du scenario"],
                ["Depense annuelle exposee", money(inputs.get("annual_spend", 0)), "Base economique du diagnostic"],
                ["CA dependant des flux import critiques", f"{inputs.get('revenue_dependency', 0)}%", "Exposition amont"],
                ["CA dependant des marches export", f"{inputs.get('export_revenue_share', 0)}%", "Exposition aval"],
            ],
            [4.8 * cm, 4.0 * cm, 7.4 * cm],
        ),
        PageBreak(),
        heading("3. Diagnostic visuel du risque"),
    ])

    charts = Table([[RiskBars(result.dimensions), RiskMatrix(result.probability, result.impact, result.global_score)]], colWidths=[10.8 * cm, 6.2 * cm])
    charts.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.extend([
        charts,
        Spacer(1, 0.2 * cm),
        table(
            ["Dimension", "Score", "Niveau", "Interpretation"],
            [
                [
                    name,
                    f"{score}/100",
                    risk_level_text(score),
                    "Zone prioritaire" if score >= 70 else "Surveillance active" if score >= 45 else "Risque contenu",
                ]
                for name, score in result.dimensions.items()
            ],
            [4.3 * cm, 2.0 * cm, 2.6 * cm, 7.3 * cm],
        ),
        p(
            "La matrice probabilite / impact permet de distinguer les risques frequents mais absorbables des risques moins probables mais critiques. "
            "Dans une logique de direction generale, l'objectif n'est pas de supprimer tout risque, mais de reduire les points de dependance qui peuvent "
            "transformer un incident externe en perte de chiffre d'affaires, rupture de service ou deterioration de marge.",
            "small",
        ),
        heading("4. Causes racines prioritaires", 2),
    ])
    for cause in result.root_causes:
        story.extend([
            KeepTogether([
                Paragraph(f"<b>{esc(cause['title'])} - {cause['severity']}/100</b>", styles["body"]),
                p(cause_explanation(cause), "small"),
            ])
        ])

    story.extend([
        PageBreak(),
        heading("5. Lecture economique"),
        p(financial_diagnosis(result)),
        table(
            ["Indicateur financier", "Montant / statut", "Interpretation"],
            [
                ["Exposition economique estimee", money(result.exposure_eur), "Base exposee au risque import-export"],
                ["Cout potentiel de non-action", money(result.non_action_cost), "Perte potentielle si aucune action n'est engagee"],
                ["Cout residuel apres actions", money(result.residual_cost), "Risque restant apres mitigation"],
                ["Gain potentiel estime", money(result.estimated_savings), "Valeur indicative du plan d'action"],
                ["Niveau de confiance", confidence_level(result), "Qualite indicative des donnees disponibles"],
            ],
            [4.8 * cm, 4.0 * cm, 7.4 * cm],
        ),
        p(
            "La lecture financiere doit etre interpretee comme une estimation de decision, pas comme une valorisation comptable definitive. "
            "Elle sert a objectiver la discussion: combien coute l'inaction, quel niveau de risque demeure apres mitigation, et quelles actions offrent "
            "le meilleur rapport valeur / effort.",
            "small",
        ),
        heading("6. Plan de mitigation priorise"),
        p(
            "Le plan de mitigation priorise les actions selon trois criteres: reduction attendue du score, faisabilite operationnelle et valeur economique indicative. "
            "La sequence recommandee est volontairement pragmatique: cartographier, diversifier, proteger les marges et installer un pilotage mensuel.",
        ),
        table(
            ["Priorite", "Horizon", "Action", "Effet", "Valeur"],
            [[a["priority"], a["horizon"], a["title"], f"-{a['score_effect']} pts", money(a["value_eur"])] for a in result.mitigation],
            [2.5 * cm, 2.1 * cm, 7.0 * cm, 2.0 * cm, 2.6 * cm],
        ),
    ])
    for action in result.mitigation[:5]:
        story.extend([
            Paragraph(f"<b>{esc(action['title'])}</b>", styles["body"]),
            p(action_explanation(action), "small"),
        ])

    story.extend([
        PageBreak(),
        heading("7. Scenarios de stress"),
        p(
            "Les stress tests traduisent le diagnostic en situations concretes. Ils permettent d'anticiper les consequences d'un choc avant qu'il ne survienne: "
            "retard client, rupture d'approvisionnement, hausse de cout, blocage reglementaire ou perte de marge.",
        ),
        table(
            ["Scenario", "Impact", "Cout estime", "Lecture"],
            [[s["name"], f"{s['impact_score']}/100", money(s["estimated_cost"]), s["description"]] for s in result.scenario_impacts],
            [4.1 * cm, 2.1 * cm, 3.0 * cm, 7.0 * cm],
        ),
        heading("8. Donnees a consolider"),
        p(
            "Les donnees ci-dessous peuvent modifier significativement le score. Les collecter permet de passer d'une estimation prudente "
            "a un diagnostic plus defensible devant un dirigeant, un financeur ou un investisseur.",
        ),
    ])
    if result.data_gaps:
        for gap in result.data_gaps:
            story.append(Paragraph(f"- {esc(gap)}", styles["body"]))
    else:
        story.append(p("Aucun manque critique identifie dans les donnees declarees."))

    story.extend([
        heading("9. Methodologie et limites"),
        p(
            "Le score CriticalRisk combine plusieurs dimensions: approvisionnement, marches export, logistique, reglementaire, prix/devise et resilience interne. "
            "Chaque dimension est estimee a partir des informations declarees dans le questionnaire et de ponderations internes du modele.",
            "small",
        ),
        p(
            "La probabilite mesure la vraisemblance d'un choc ou d'une degradation operationnelle. L'impact mesure la consequence economique et operationnelle potentielle. "
            "Le score global combine ces deux axes afin de prioriser les decisions de mitigation.",
            "small",
        ),
        p(
            "Ce rapport constitue une aide a la decision. Il ne remplace pas un audit juridique, douanier, financier ou assurantiel. "
            "Les estimations doivent etre confirmees avec contrats, volumes, historique prix, pays fournisseurs, pays clients, incoterms, clauses de paiement et plans de continuite.",
            "small",
        ),
    ])

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
