from datetime import date
import io


def money(value):
    return f"{int(value):,}".replace(",", " ") + " EUR"


def build_text_report(company, inputs, result):
    lines = [
        "CriticalRisk Intelligence - Rapport de diagnostic",
        f"Date: {date.today().strftime('%d/%m/%Y')}",
        "",
        f"Entreprise: {company or 'Non renseignee'}",
        f"Profil international: {inputs.get('trade_profile', 'Non renseigne')}",
        f"Secteur: {inputs['sector']}",
        f"Flux, matieres ou composants critiques: {', '.join(inputs['materials'])}",
        "",
        f"Score global: {result.global_score}/100",
        f"Score cible apres mitigation: {result.target_score}/100",
        f"Niveau de risque: {result.level}",
        f"Probabilite: {result.probability}/100",
        f"Impact: {result.impact}/100",
        "",
        f"Exposition economique estimee: {money(result.exposure_eur)}",
        f"Cout potentiel de non-action: {money(result.non_action_cost)}",
        f"Cout residuel estime apres actions: {money(result.residual_cost)}",
        f"Gain potentiel estime: {money(result.estimated_savings)}",
        "",
        "Synthese dirigeant:",
        result.executive_summary,
        "",
        "Causes racines:",
    ]

    for cause in result.root_causes:
        lines.append(f"- {cause['title']} ({cause['severity']}/100): {cause['detail']}")

    lines.extend([
        "",
        "Dimensions de risque:",
    ])

    for name, score in result.dimensions.items():
        lines.append(f"- {name}: {score}/100")

    lines.extend(["", "Plan de mitigation:"])
    for action in result.mitigation:
        lines.append(
            f"- [{action['horizon']}] {action['title']} - {action['detail']} "
            f"KPI: {action['kpi']} | Effort: {action['effort']} | Impact: {action['impact']} "
            f"| Effet score: -{action['score_effect']} pts | Valeur estimee: {money(action['value_eur'])}"
        )

    lines.extend(["", "Scenarios de stress:"])
    for scenario in result.scenario_impacts:
        lines.append(f"- {scenario['name']}: impact {scenario['impact_score']}/100, cout estime {money(scenario['estimated_cost'])}")

    if result.data_gaps:
        lines.extend(["", "Donnees a collecter:"])
        for gap in result.data_gaps:
            lines.append(f"- {gap}")

    return "\n".join(lines)


def build_pdf(company, inputs, result):
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_left_margin(12)
    pdf.set_right_margin(12)
    pdf.add_page()

    pdf.set_fill_color(11, 18, 32)
    pdf.rect(0, 0, 210, 24, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 14, "CriticalRisk Intelligence", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "Diagnostic et mitigation des risques de commerce international", ln=True)

    pdf.ln(12)
    pdf.set_text_color(20, 24, 36)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Synthese du risque", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Entreprise: {company or 'Non renseignee'}", ln=True)
    pdf.cell(0, 7, f"Profil international: {inputs.get('trade_profile', 'Non renseigne')}", ln=True)
    pdf.cell(0, 7, f"Secteur: {inputs['sector']}", ln=True)
    pdf.multi_cell(0, 7, f"Flux, matieres ou composants critiques: {', '.join(inputs['materials'])}")

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 24)
    if result.global_score >= 75:
        pdf.set_text_color(220, 38, 38)
    elif result.global_score >= 55:
        pdf.set_text_color(234, 88, 12)
    elif result.global_score >= 35:
        pdf.set_text_color(212, 160, 65)
    else:
        pdf.set_text_color(22, 163, 74)
    pdf.cell(0, 12, f"{result.global_score}/100 - Risque {result.level}", ln=True)
    pdf.set_text_color(20, 24, 36)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Score cible apres actions: {result.target_score}/100", ln=True)
    pdf.cell(0, 7, f"Probabilite: {result.probability}/100 | Impact: {result.impact}/100", ln=True)
    pdf.cell(0, 7, f"Cout potentiel de non-action: {money(result.non_action_cost)}", ln=True)
    pdf.cell(0, 7, f"Gain potentiel estime: {money(result.estimated_savings)}", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Synthese dirigeant", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(186, 5, result.executive_summary)

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Causes racines", ln=True)
    pdf.set_font("Helvetica", "", 9)
    for cause in result.root_causes:
        pdf.set_x(12)
        pdf.set_font("Helvetica", "B", 9)
        pdf.multi_cell(186, 5, f"{cause['title']} ({cause['severity']}/100)")
        pdf.set_x(12)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(186, 5, cause["detail"])
        pdf.ln(1)

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Plan de mitigation", ln=True)
    pdf.set_font("Helvetica", "", 9)
    for action in result.mitigation:
        pdf.set_x(12)
        pdf.set_font("Helvetica", "B", 9)
        pdf.multi_cell(186, 5, f"{action['horizon']} - {action['title']}")
        pdf.set_x(12)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(186, 5, action["detail"])
        pdf.set_x(12)
        pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(
            186,
            5,
            f"KPI: {action['kpi']} | Effort: {action['effort']} | Impact: {action['impact']} | "
            f"Effet score: -{action['score_effect']} pts | Valeur: {money(action['value_eur'])}",
        )
        pdf.set_text_color(20, 24, 36)
        pdf.ln(2)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Scenarios de stress", ln=True)
    pdf.set_font("Helvetica", "", 9)
    for scenario in result.scenario_impacts:
        pdf.set_x(12)
        pdf.multi_cell(186, 5, f"{scenario['name']}: impact {scenario['impact_score']}/100, cout estime {money(scenario['estimated_cost'])}")

    if result.data_gaps:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Donnees a collecter", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for gap in result.data_gaps:
            pdf.set_x(12)
            pdf.multi_cell(186, 5, f"- {gap}")

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf.read()
