from datetime import date
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
        from fpdf import FPDF
    except ImportError:
        return None

    class ReportPDF(FPDF):
        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(110, 118, 130)
            self.cell(0, 8, f"CriticalRisk Intelligence | Rapport confidentiel | Page {self.page_no()}", align="C")

    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_left_margin(14)
    pdf.set_right_margin(14)

    def clean(text):
        return str(text).replace("’", "'").replace("–", "-").replace("—", "-")

    def section(title):
        pdf.ln(4)
        pdf.set_text_color(11, 18, 32)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, clean(title), ln=True)
        pdf.set_draw_color(245, 185, 66)
        pdf.set_line_width(.6)
        pdf.line(14, pdf.get_y(), 196, pdf.get_y())
        pdf.ln(4)

    def paragraph(text, size=9, line_height=5):
        pdf.set_text_color(38, 45, 58)
        pdf.set_font("Helvetica", "", size)
        pdf.multi_cell(182, line_height, clean(text))

    def label_value(label, value, width=60):
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(85, 95, 110)
        pdf.cell(width, 5, clean(label), ln=False)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(20, 24, 36)
        pdf.multi_cell(182 - width, 5, clean(value))

    def score_color(score):
        if score >= 75:
            return 220, 38, 38
        if score >= 55:
            return 234, 88, 12
        if score >= 35:
            return 212, 160, 65
        return 22, 163, 74

    def kpi_box(x, y, w, title, value, subtitle, color=(11, 18, 32)):
        pdf.set_xy(x, y)
        pdf.set_fill_color(247, 249, 252)
        pdf.set_draw_color(220, 226, 235)
        pdf.rect(x, y, w, 28, "DF")
        pdf.set_xy(x + 4, y + 4)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(96, 108, 124)
        pdf.cell(w - 8, 4, clean(title), ln=True)
        pdf.set_x(x + 4)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*color)
        pdf.cell(w - 8, 8, clean(value), ln=True)
        pdf.set_x(x + 4)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(96, 108, 124)
        pdf.multi_cell(w - 8, 4, clean(subtitle))

    def simple_table(headers, rows, widths, line_height=6):
        pdf.set_fill_color(11, 18, 32)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 7)
        for header, width in zip(headers, widths):
            pdf.cell(width, line_height, clean(header), border=1, fill=True)
        pdf.ln(line_height)

        pdf.set_font("Helvetica", "", 7)
        for row_index, row in enumerate(rows):
            fill = row_index % 2 == 0
            pdf.set_fill_color(248, 250, 252 if fill else 255)
            pdf.set_text_color(35, 45, 60)
            y_start = pdf.get_y()
            x_start = pdf.get_x()
            max_lines = 1
            for value, width in zip(row, widths):
                text_width = max(width - 3, 8)
                approx_chars = max(int(text_width / 1.7), 10)
                lines = max(1, (len(clean(value)) // approx_chars) + 1)
                max_lines = max(max_lines, lines)
            row_height = min(max_lines, 3) * 4.2 + 2
            for value, width in zip(row, widths):
                pdf.set_xy(x_start, y_start)
                pdf.multi_cell(width, 4.2, clean(value), border=1, fill=fill)
                x_start += width
            pdf.set_y(y_start + row_height)

    def dimensions_bar_chart(x, y, w, h):
        pdf.set_xy(x, y)
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(220, 226, 235)
        pdf.rect(x, y, w, h, "DF")
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(11, 18, 32)
        pdf.set_xy(x + 4, y + 3)
        pdf.cell(w - 8, 5, "Graphique des dimensions de risque", ln=True)

        bar_x = x + 48
        bar_w = w - 60
        current_y = y + 13
        for name, score in result.dimensions.items():
            r, g, b = score_color(score)
            pdf.set_font("Helvetica", "", 6.8)
            pdf.set_text_color(60, 70, 85)
            pdf.set_xy(x + 4, current_y - 1)
            pdf.cell(42, 4, clean(name[:22]))
            pdf.set_fill_color(230, 235, 242)
            pdf.rect(bar_x, current_y, bar_w, 3.4, "F")
            pdf.set_fill_color(r, g, b)
            pdf.rect(bar_x, current_y, bar_w * score / 100, 3.4, "F")
            pdf.set_xy(bar_x + bar_w + 2, current_y - 1)
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(11, 18, 32)
            pdf.cell(10, 4, f"{score}")
            current_y += 7

    def risk_matrix(x, y, size):
        pdf.set_xy(x, y)
        cell = size / 3
        zones = [
            ((226, 245, 235), "Faible"),
            ((255, 248, 220), "Modere"),
            ((255, 238, 226), "Eleve"),
            ((255, 248, 220), "Modere"),
            ((255, 238, 226), "Eleve"),
            ((255, 226, 226), "Critique"),
            ((255, 238, 226), "Eleve"),
            ((255, 226, 226), "Critique"),
            ((255, 226, 226), "Critique"),
        ]
        idx = 0
        for row in range(3):
            for col in range(3):
                color, label = zones[idx]
                pdf.set_fill_color(*color)
                pdf.set_draw_color(220, 226, 235)
                pdf.rect(x + col * cell, y + row * cell, cell, cell, "DF")
                pdf.set_font("Helvetica", "", 6)
                pdf.set_text_color(95, 105, 120)
                pdf.set_xy(x + col * cell + 2, y + row * cell + 2)
                pdf.cell(cell - 4, 3, label)
                idx += 1

        px = x + (result.probability / 100) * size
        py = y + size - (result.impact / 100) * size
        pdf.set_fill_color(*score_color(result.global_score))
        pdf.ellipse(px - 2.2, py - 2.2, 4.4, 4.4, "F")
        pdf.set_draw_color(11, 18, 32)
        pdf.rect(x, y, size, size)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(11, 18, 32)
        pdf.set_xy(x, y - 7)
        pdf.cell(size, 5, "Matrice probabilite / impact", align="C")
        pdf.set_font("Helvetica", "", 6)
        pdf.set_xy(x, y + size + 2)
        pdf.cell(size, 4, "Probabilite ->", align="C")
        pdf.set_xy(x - 10, y + size / 2 - 3)
        pdf.cell(8, 4, "Impact", align="R")

    # Cover page
    pdf.add_page()
    pdf.set_fill_color(7, 16, 29)
    pdf.rect(0, 0, 210, 72, "F")
    pdf.set_text_color(245, 185, 66)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(14, 16)
    pdf.cell(0, 7, "CRITICALRISK INTELLIGENCE", ln=True)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_x(14)
    pdf.multi_cell(172, 10, "Rapport de diagnostic import-export")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_x(14)
    pdf.multi_cell(172, 6, "Analyse des risques, cout de non-action et plan de mitigation priorise")

    pdf.set_y(88)
    label_value("Entreprise", company or "Non renseignee")
    label_value("Profil international", inputs.get("trade_profile", "Non renseigne"))
    label_value("Secteur", inputs["sector"])
    label_value("Flux critiques", ", ".join(inputs["materials"]))
    label_value("Date d'emission", date.today().strftime("%d/%m/%Y"))

    kpi_y = 134
    kpi_box(14, kpi_y, 42, "SCORE ACTUEL", f"{result.global_score}/100", result.level, score_color(result.global_score))
    kpi_box(60, kpi_y, 42, "SCORE CIBLE", f"{result.target_score}/100", f"-{result.score_reduction} pts", (22, 163, 74))
    kpi_box(106, kpi_y, 42, "COUT NON-ACTION", money(result.non_action_cost), "estimation", (220, 38, 38))
    kpi_box(152, kpi_y, 44, "GAIN POTENTIEL", money(result.estimated_savings), "apres actions", (22, 163, 74))

    pdf.set_y(176)
    section("Synthese decisionnelle")
    paragraph(decision_recommendation(result), size=10, line_height=6)
    paragraph(result.executive_summary, size=10, line_height=6)

    pdf.set_y(250)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(110, 118, 130)
    pdf.multi_cell(182, 4, "Document genere automatiquement. Les estimations doivent etre consolidees avec les donnees contractuelles, operationnelles et financieres de l'entreprise.")

    # Analysis page
    pdf.add_page()
    section("1. Profil analyse")
    simple_table(
        ["Indicateur", "Valeur", "Lecture"],
        [
            ["Depense annuelle exposee", money(inputs.get("annual_spend", 0)), "Base economique du diagnostic"],
            ["CA dependant des flux import critiques", f"{inputs.get('revenue_dependency', 0)}%", "Exposition amont"],
            ["CA dependant des marches export", f"{inputs.get('export_revenue_share', 0)}%", "Exposition aval"],
            ["Fournisseurs qualifies", str(inputs.get("suppliers", 0)), "Diversification fournisseur"],
            ["Part fournisseur principal", f"{inputs.get('single_supplier_share', 0)}%", "Risque de concentration"],
            ["Stock tampon", f"{inputs.get('stock_weeks', 0)} semaines", "Capacite d'absorption court terme"],
        ],
        [64, 36, 82],
    )

    section("2. Dimensions de risque")
    chart_y = pdf.get_y()
    dimensions_bar_chart(14, chart_y, 116, 62)
    risk_matrix(140, chart_y + 4, 52)
    pdf.set_y(chart_y + 70)
    simple_table(
        ["Dimension", "Score", "Niveau"],
        [[name, f"{score}/100", risk_level_text(score)] for name, score in result.dimensions.items()],
        [82, 30, 70],
    )

    section("3. Causes racines prioritaires")
    for cause in result.root_causes:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(11, 18, 32)
        pdf.multi_cell(182, 5, clean(f"{cause['title']} - {cause['severity']}/100"))
        paragraph(cause["detail"], size=9)
        pdf.ln(1)

    section("4. Lecture economique")
    simple_table(
        ["Indicateur financier", "Montant / statut", "Interpretation"],
        [
            ["Exposition economique estimee", money(result.exposure_eur), "Base exposee au risque import-export"],
            ["Cout potentiel de non-action", money(result.non_action_cost), "Perte potentielle si aucune action n'est engagee"],
            ["Cout residuel apres actions", money(result.residual_cost), "Risque restant apres mitigation"],
            ["Gain potentiel estime", money(result.estimated_savings), "Valeur economique indicative du plan d'action"],
            ["Niveau de confiance", confidence_level(result), "Qualite indicative des donnees disponibles"],
        ],
        [58, 48, 76],
    )

    # Action page
    pdf.add_page()
    section("5. Plan de mitigation priorise")
    simple_table(
        ["Priorite", "Horizon", "Action", "Effet", "Valeur"],
        [
            [
                action["priority"],
                action["horizon"],
                action["title"],
                f"-{action['score_effect']} pts",
                money(action["value_eur"]),
            ]
            for action in result.mitigation
        ],
        [28, 24, 74, 22, 34],
    )
    pdf.ln(4)
    for action in result.mitigation:
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(220, 226, 235)
        x = 14
        y = pdf.get_y()
        pdf.rect(x, y, 182, 30, "DF")
        pdf.set_xy(x + 4, y + 4)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(11, 18, 32)
        pdf.multi_cell(174, 5, clean(f"{action['priority']} | {action['horizon']} | {action['title']}"))
        pdf.set_x(x + 4)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(50, 60, 74)
        pdf.multi_cell(174, 4, clean(action["detail"]))
        pdf.set_x(x + 4)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(90, 100, 116)
        pdf.multi_cell(
            174,
            4,
            clean(
                f"KPI: {action['kpi']} | Effort: {action['effort']} | Impact: {action['impact']} | "
                f"Effet score: -{action['score_effect']} pts | Valeur estimee: {money(action['value_eur'])}"
            ),
        )
        pdf.ln(4)

    section("6. Scenarios de stress")
    simple_table(
        ["Scenario", "Impact", "Cout estime", "Lecture"],
        [
            [
                scenario["name"],
                f"{scenario['impact_score']}/100",
                money(scenario["estimated_cost"]),
                scenario["description"],
            ]
            for scenario in result.scenario_impacts
        ],
        [48, 22, 36, 76],
    )
    pdf.ln(4)
    for scenario in result.scenario_impacts:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(11, 18, 32)
        pdf.multi_cell(182, 5, clean(f"{scenario['name']} | Impact {scenario['impact_score']}/100 | Cout {money(scenario['estimated_cost'])}"))
        paragraph(scenario["description"], size=8)
        pdf.ln(1)

    # Appendix page
    pdf.add_page()
    section("7. Donnees a consolider")
    if result.data_gaps:
        for gap in result.data_gaps:
            paragraph(f"- {gap}", size=9)
    else:
        paragraph("Aucun manque critique identifie dans les donnees declarees.", size=9)

    section("8. Methodologie")
    paragraph(
        "Le score CriticalRisk combine plusieurs dimensions: approvisionnement, marches export, logistique, reglementaire, prix/devise et resilience interne. "
        "Chaque dimension est estimee a partir des informations declarees dans le questionnaire et des ponderations internes du modele.",
        size=9,
    )
    paragraph(
        "La probabilite mesure la vraisemblance d'un choc ou d'une degradation operationnelle. L'impact mesure la consequence economique et operationnelle potentielle. "
        "Le score global combine ces deux axes afin de prioriser les decisions de mitigation.",
        size=9,
    )

    section("9. Limites et prochaines etapes")
    paragraph(
        "Ce rapport constitue une aide a la decision. Il ne remplace pas un audit juridique, douanier, financier ou assurantiel. "
        "Les estimations doivent etre confirmees avec contrats, volumes, historique prix, pays fournisseurs, pays clients, incoterms, clauses de paiement et plans de continuite.",
        size=9,
    )
    paragraph(
        "Prochaine etape recommandee: consolider les donnees manquantes, valider les hypotheses avec les equipes achats, finance et operations, puis simuler un scenario cible apres mitigation.",
        size=9,
    )

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf.read()
