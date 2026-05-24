from copy import deepcopy
from datetime import date
import html

import plotly.graph_objects as go
import streamlit as st

from data import MATERIAL_RISK, PERSONAS, SECTORS, TRADE_PROFILES
from market_data import (
    fetch_ecb_rates,
    fetch_gdelt_alerts,
    fetch_market_quotes,
    fetch_world_bank_context,
    market_pressure_score,
)
from reporting import build_pdf, build_text_report, money
from risk_engine import calculate_risk, level_color


st.set_page_config(
    page_title="CriticalRisk Intelligence",
    page_icon="CR",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    :root {
        --bg:#07101d;
        --panel:#111827;
        --panel2:#172033;
        --line:rgba(255,255,255,.09);
        --text:#f8fafc;
        --muted:#9fb0c5;
        --soft:#5e7188;
        --accent:#f5b942;
        --green:#22c55e;
        --red:#ef4444;
        --orange:#f97316;
        --cyan:#38bdf8;
    }
    .stApp { background:var(--bg); color:var(--text); }
    .block-container { padding-top:1.6rem; max-width:1240px; }
    h1, h2, h3 { color:var(--text) !important; letter-spacing:0 !important; }
    p, label, span, div { letter-spacing:0 !important; }
    [data-testid="stSidebar"] { background:#050b14; border-right:1px solid var(--line); }
    [data-testid="stSidebar"] * { color:var(--muted) !important; }
    .hero {
        display:flex;
        justify-content:space-between;
        gap:1rem;
        align-items:flex-end;
        padding:.8rem 0 1.1rem;
        border-bottom:1px solid var(--line);
        margin-bottom:1.1rem;
    }
    .eyebrow {
        color:var(--accent);
        font-size:.88rem;
        font-weight:900;
        text-transform:uppercase;
    }
    .brand-title {
        margin:.25rem 0 .15rem;
        font-size:3.25rem;
        line-height:.95;
        font-weight:950;
        color:var(--text);
    }
    .hero h1 { margin:.3rem 0 0; font-size:1.5rem; line-height:1.18; color:var(--accent) !important; }
    .hero p { color:var(--muted); max-width:820px; margin:.65rem 0 0; line-height:1.55; }
    .panel, .player-card, .action-card, .cause-card {
        background:linear-gradient(180deg,var(--panel),#0d1626);
        border:1px solid var(--line);
        border-radius:8px;
        padding:1rem;
    }
    .player-card {
        min-height:226px;
        border-color:rgba(245,185,66,.35);
        box-shadow:0 0 0 1px rgba(245,185,66,.05) inset;
    }
    .rating {
        font-size:3.1rem;
        line-height:1;
        font-weight:950;
    }
    .rating-label {
        color:var(--soft);
        font-weight:900;
        font-size:.75rem;
        text-transform:uppercase;
    }
    .stat-row {
        display:flex;
        align-items:center;
        gap:.5rem;
        margin:.38rem 0;
    }
    .stat-code {
        width:42px;
        color:var(--muted);
        font-weight:900;
        font-size:.78rem;
    }
    .stat-bar {
        flex:1;
        height:8px;
        border-radius:99px;
        background:#243149;
        overflow:hidden;
    }
    .stat-fill {
        height:100%;
        border-radius:99px;
    }
    .stat-value {
        width:34px;
        color:var(--text);
        font-weight:900;
        text-align:right;
        font-size:.8rem;
    }
    .metric-grid {
        display:grid;
        grid-template-columns:repeat(5,minmax(0,1fr));
        gap:.7rem;
        margin:.8rem 0 1rem;
    }
    .metric-card {
        background:var(--panel);
        border:1px solid var(--line);
        border-radius:8px;
        padding:.85rem;
    }
    .metric-label {
        color:var(--soft);
        font-size:.68rem;
        text-transform:uppercase;
        font-weight:900;
    }
    .metric-value {
        font-size:1.35rem;
        font-weight:950;
        margin-top:.2rem;
    }
    .small-muted { color:var(--muted); font-size:.82rem; line-height:1.5; }
    .pill {
        display:inline-block;
        border-radius:999px;
        padding:.18rem .55rem;
        font-size:.72rem;
        font-weight:800;
        border:1px solid var(--line);
        color:var(--muted);
    }
    .action-title { color:var(--text); font-weight:900; margin:.35rem 0; }
    .action-meta { color:var(--accent); font-size:.72rem; text-transform:uppercase; font-weight:900; }
    .cause-grid {
        display:grid;
        grid-template-columns:repeat(3,minmax(0,1fr));
        gap:.75rem;
        margin:.7rem 0 1rem;
    }
    .summary-box {
        background:linear-gradient(135deg,rgba(245,185,66,.16),rgba(56,189,248,.08));
        border:1px solid rgba(245,185,66,.28);
        border-radius:8px;
        padding:1rem 1.1rem;
        color:var(--text);
        line-height:1.6;
    }
    .decision-grid {
        display:grid;
        grid-template-columns:repeat(4,minmax(0,1fr));
        gap:.7rem;
        margin:.8rem 0;
    }
    .decision-tile {
        background:#0f172a;
        border:1px solid var(--line);
        border-radius:8px;
        padding:.75rem;
        min-height:92px;
    }
    .decision-tile strong {
        display:block;
        color:var(--text);
        font-size:1.15rem;
        margin:.2rem 0;
    }
    .context-band {
        display:flex;
        flex-wrap:wrap;
        gap:.45rem;
        margin:.55rem 0 .85rem;
    }
    .stButton > button, .stDownloadButton > button {
        border-radius:8px !important;
        border:1px solid rgba(245,185,66,.4) !important;
        background:#f5b942 !important;
        color:#111827 !important;
        font-weight:900 !important;
    }
    @media (max-width: 900px) {
        .hero { display:block; }
        .brand-title { font-size:2.25rem; }
        .metric-grid, .cause-grid, .decision-grid { grid-template-columns:1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def esc(value):
    return html.escape(str(value))


def default_scenario(name="Scenario actuel"):
    return {
        "scenario_name": name,
        "company": "",
        "persona": PERSONAS[0],
        "trade_profile": "Importateur et exportateur",
        "sector": "Electronique",
        "supplier_country": "CHN",
        "destination_country": "USA",
        "materials": ["Semi-conducteurs", "RAM"],
        "suppliers": 1,
        "single_supplier_share": 80,
        "stock_weeks": 4,
        "substitution_months": 9,
        "annual_spend": 500000,
        "revenue_dependency": 35,
        "export_revenue_share": 30,
        "destination_concentration": 45,
        "payment_risk": 35,
        "fx_exposure": 40,
        "customs_complexity": 45,
        "sanctions_exposure": 20,
        "risk_maturity": 30,
        "contract_coverage": 35,
        "price_hedging": 20,
        "logistics_diversity": 30,
        "monitoring": 30,
        "incident_history": 20,
    }


def init_state():
    if "scenarios" not in st.session_state:
        base = default_scenario()
        mitigated = deepcopy(base)
        mitigated.update({
            "scenario_name": "Plan mitigation",
            "suppliers": 3,
            "single_supplier_share": 45,
            "stock_weeks": 10,
            "substitution_months": 5,
            "risk_maturity": 65,
            "contract_coverage": 70,
            "price_hedging": 55,
            "logistics_diversity": 65,
            "monitoring": 70,
            "incident_history": 10,
        })
        st.session_state.scenarios = {
            base["scenario_name"]: base,
            mitigated["scenario_name"]: mitigated,
        }
    if "active_scenario" not in st.session_state:
        st.session_state.active_scenario = list(st.session_state.scenarios.keys())[0]


def active_payload():
    return st.session_state.scenarios[st.session_state.active_scenario]


def save_active(payload):
    old_name = st.session_state.active_scenario
    new_name = payload["scenario_name"].strip() or old_name
    payload["scenario_name"] = new_name
    if new_name != old_name:
        st.session_state.scenarios.pop(old_name, None)
        st.session_state.active_scenario = new_name
    st.session_state.scenarios[new_name] = payload


def calculate_all():
    return {
        name: calculate_risk(payload)
        for name, payload in st.session_state.scenarios.items()
    }


def render_header():
    st.markdown(
        """
        <div class="hero">
            <div>
                <div class="eyebrow">CriticalRisk Intelligence</div>
                <div class="brand-title">CriticalRisk</div>
                <h1>Intelligence risque import-export.</h1>
                <p>
                Creez plusieurs scenarios, comparez les scores, visualisez les indicateurs de commerce international,
                positionnez chaque scenario sur la matrice probabilite/impact et exportez un rapport PDF.
                </p>
            </div>
            <span class="pill">Profil · Questionnaire · Score · Radar · Matrice · PDF</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scenario_sidebar():
    with st.sidebar:
        st.markdown("### Scenarios")
        names = list(st.session_state.scenarios.keys())
        selected = st.selectbox(
            "Scenario actif",
            names,
            index=names.index(st.session_state.active_scenario),
        )
        st.session_state.active_scenario = selected

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Nouveau", width="stretch"):
                idx = len(st.session_state.scenarios) + 1
                name = f"Scenario {idx}"
                st.session_state.scenarios[name] = default_scenario(name)
                st.session_state.active_scenario = name
                st.rerun()
        with col_b:
            if st.button("Dupliquer", width="stretch"):
                base = deepcopy(active_payload())
                name = f"{base['scenario_name']} copie"
                base["scenario_name"] = name
                st.session_state.scenarios[name] = base
                st.session_state.active_scenario = name
                st.rerun()

        if len(st.session_state.scenarios) > 1:
            if st.button("Supprimer scenario actif", width="stretch"):
                st.session_state.scenarios.pop(st.session_state.active_scenario)
                st.session_state.active_scenario = list(st.session_state.scenarios.keys())[0]
                st.rerun()

        st.divider()
        results = calculate_all()
        best = min(results.items(), key=lambda item: item[1].global_score)
        worst = max(results.items(), key=lambda item: item[1].global_score)
        st.markdown(f"**Meilleur:** {best[0]} · {best[1].global_score}/100")
        st.markdown(f"**Plus expose:** {worst[0]} · {worst[1].global_score}/100")


def scenario_editor(payload):
    edited = deepcopy(payload)

    tab_profile, tab_questions = st.tabs(["Profil entreprise", "Questionnaire"])

    with tab_profile:
        c1, c2, c3 = st.columns([1.2, 1, 1])
        with c1:
            edited["scenario_name"] = st.text_input("Nom du scenario", value=edited["scenario_name"])
            edited["company"] = st.text_input("Entreprise", value=edited.get("company", ""))
            edited["persona"] = st.selectbox("Persona", PERSONAS, index=PERSONAS.index(edited["persona"]))
            trade_profile = edited.get("trade_profile", TRADE_PROFILES[0])
            if trade_profile not in TRADE_PROFILES:
                trade_profile = TRADE_PROFILES[0]
            edited["trade_profile"] = st.selectbox(
                "Profil international",
                TRADE_PROFILES,
                index=TRADE_PROFILES.index(trade_profile),
            )
        with c2:
            sector_names = list(SECTORS.keys())
            selected_sector = st.selectbox("Secteur", sector_names, index=sector_names.index(edited["sector"]))
            if selected_sector != edited["sector"]:
                edited["sector"] = selected_sector
                edited["materials"] = SECTORS[selected_sector]["materials"][:2]
            edited["materials"] = st.multiselect(
                "Matieres / composants critiques",
                sorted(MATERIAL_RISK.keys()),
                default=edited["materials"],
                max_selections=5,
            )
            if not edited["materials"]:
                edited["materials"] = SECTORS[edited["sector"]]["materials"][:1]
        with c3:
            country_labels = list(COUNTRY_OPTIONS.keys())
            supplier_code = edited.get("supplier_country", "CHN")
            destination_code = edited.get("destination_country", "USA")
            supplier_label = country_label_from_code(supplier_code)
            destination_label = country_label_from_code(destination_code)
            if supplier_label not in country_labels:
                supplier_label = "Chine"
            if destination_label not in country_labels:
                destination_label = "Etats-Unis"
            edited["supplier_country"] = COUNTRY_OPTIONS[
                st.selectbox("Pays fournisseur principal", country_labels, index=country_labels.index(supplier_label))
            ]
            edited["destination_country"] = COUNTRY_OPTIONS[
                st.selectbox("Pays client / marche prioritaire", country_labels, index=country_labels.index(destination_label))
            ]
            edited["annual_spend"] = st.number_input(
                "Depense annuelle exposee (EUR)",
                min_value=0,
                step=50000,
                value=int(edited["annual_spend"]),
            )
            edited["revenue_dependency"] = st.slider(
                "CA dependant des flux import critiques (%)",
                0,
                100,
                int(edited["revenue_dependency"]),
            )
            edited["export_revenue_share"] = st.slider(
                "CA dependant des marches export (%)",
                0,
                100,
                int(edited.get("export_revenue_share", 0)),
            )

    with tab_questions:
        st.caption("Ces questions pilotent les indicateurs. Modifiez-les pour construire vos scenarios.")
        q1, q2, q3 = st.columns(3)
        with q1:
            edited["suppliers"] = st.number_input(
                "Fournisseurs qualifies",
                min_value=1,
                max_value=20,
                value=int(edited["suppliers"]),
            )
            edited["single_supplier_share"] = st.slider(
                "Part du fournisseur principal (%)",
                0,
                100,
                int(edited["single_supplier_share"]),
            )
            edited["stock_weeks"] = st.slider(
                "Stock tampon disponible (semaines)",
                0,
                24,
                int(edited["stock_weeks"]),
            )
        with q2:
            edited["substitution_months"] = st.slider(
                "Delai de substitution / requalification (mois)",
                0,
                24,
                int(edited["substitution_months"]),
            )
            edited["contract_coverage"] = st.slider(
                "Couverture contractuelle long terme (%)",
                0,
                100,
                int(edited["contract_coverage"]),
            )
            edited["price_hedging"] = st.slider(
                "Couverture prix / clauses anti-volatilite (%)",
                0,
                100,
                int(edited["price_hedging"]),
            )
        with q3:
            edited["logistics_diversity"] = st.slider(
                "Diversite logistique / zones alternatives (%)",
                0,
                100,
                int(edited["logistics_diversity"]),
            )
            edited["risk_maturity"] = st.slider(
                "Maturite gestion des risques (%)",
                0,
                100,
                int(edited["risk_maturity"]),
            )
            edited["monitoring"] = st.slider(
                "Veille marche et alertes (%)",
                0,
                100,
                int(edited["monitoring"]),
            )
            edited["incident_history"] = st.slider(
                "Historique incidents subis (%)",
                0,
                100,
                int(edited["incident_history"]),
            )
        q4, q5, q6 = st.columns(3)
        with q4:
            edited["destination_concentration"] = st.slider(
                "Concentration pays clients export (%)",
                0,
                100,
                int(edited.get("destination_concentration", 0)),
            )
            edited["customs_complexity"] = st.slider(
                "Complexite douane / incoterms (%)",
                0,
                100,
                int(edited.get("customs_complexity", 30)),
            )
        with q5:
            edited["sanctions_exposure"] = st.slider(
                "Exposition sanctions / export control (%)",
                0,
                100,
                int(edited.get("sanctions_exposure", 15)),
            )
            edited["payment_risk"] = st.slider(
                "Risque paiement client / contrepartie (%)",
                0,
                100,
                int(edited.get("payment_risk", 20)),
            )
        with q6:
            edited["fx_exposure"] = st.slider(
                "Exposition devise (%)",
                0,
                100,
                int(edited.get("fx_exposure", 25)),
            )

    if st.button("Enregistrer ce scenario", width="stretch"):
        save_active(edited)
        st.success("Scenario enregistre.")
        st.rerun()

    return edited


def stat_color(value):
    if value >= 75:
        return "#ef4444"
    if value >= 55:
        return "#f97316"
    if value >= 35:
        return "#f5b942"
    return "#22c55e"


def stat_rows(result):
    return [
        ("APP", result.dimensions["Approvisionnement"]),
        ("EXP", result.dimensions["Marches export"]),
        ("LOG", result.dimensions["Logistique"]),
        ("REG", result.dimensions["Reglementaire"]),
        ("FX", result.dimensions["Prix et devise"]),
        ("RES", result.dimensions["Resilience interne"]),
        ("IMP", result.impact),
    ]


def render_player_card(name, result, compact=False):
    rows = stat_rows(result)
    rows_html = ""
    for code, value in rows:
        rows_html += (
            f"<div class='stat-row'>"
            f"<div class='stat-code'>{code}</div>"
            f"<div class='stat-bar'><div class='stat-fill' style='width:{value}%;background:{stat_color(value)}'></div></div>"
            f"<div class='stat-value'>{value}</div>"
            f"</div>"
        )

    st.markdown(
        f"""
        <div class="player-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:.75rem">
                <div>
                    <div class="rating" style="color:{level_color(result.global_score)}">{result.global_score}</div>
                    <div class="rating-label">RISQUE {esc(result.level)}</div>
                </div>
                <div style="text-align:right">
                    <div class="action-title">{esc(name)}</div>
                    <span class="pill">Cible {result.target_score}</span>
                </div>
            </div>
            <div style="margin-top:.8rem">{rows_html}</div>
            <div class="small-muted" style="margin-top:.7rem">
                Gain potentiel: <b>{money(result.estimated_savings)}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(result):
    items = [
        ("Score actuel", f"{result.global_score}/100", level_color(result.global_score)),
        ("Score cible", f"{result.target_score}/100", "#22c55e"),
        ("Probabilite", f"{result.probability}/100", "#f5b942"),
        ("Impact", f"{result.impact}/100", "#38bdf8"),
        ("Gain potentiel", money(result.estimated_savings), "#fb7185"),
    ]
    html_items = ""
    for label, value, color in items:
        html_items += (
            f"<div class='metric-card'>"
            f"<div class='metric-label'>{esc(label)}</div>"
            f"<div class='metric-value' style='color:{color}'>{esc(value)}</div>"
            f"</div>"
        )
    st.markdown(f"<div class='metric-grid'>{html_items}</div>", unsafe_allow_html=True)


DIMENSION_LABELS = {
    "Approvisionnement": "Dependance amont, concentration fournisseur, stock et capacite de substitution.",
    "Marches export": "Dependance aux pays clients, concentration aval et exposition commerciale internationale.",
    "Logistique": "Routes, delais, diversite de transport et capacite d'absorption en cas de blocage.",
    "Reglementaire": "Douane, sanctions, export control, licences, incoterms et contraintes pays.",
    "Prix et devise": "Volatilite matieres, energie, devise, paiement et clauses de couverture.",
    "Resilience interne": "Maturite de pilotage, veille, gouvernance risque et capacite de reaction.",
}


COUNTRY_OPTIONS = {
    "Chine": "CHN",
    "Etats-Unis": "USA",
    "Allemagne": "DEU",
    "France": "FRA",
    "Italie": "ITA",
    "Espagne": "ESP",
    "Royaume-Uni": "GBR",
    "Turquie": "TUR",
    "Maroc": "MAR",
    "Inde": "IND",
    "Vietnam": "VNM",
    "Japon": "JPN",
    "Coree du Sud": "KOR",
    "Mexique": "MEX",
    "Bresil": "BRA",
    "Afrique du Sud": "ZAF",
}


def country_label_from_code(code):
    for label, option_code in COUNTRY_OPTIONS.items():
        if option_code == code:
            return label
    return code or "Non renseigne"


MARKET_EXPOSURE_MAP = {
    "Cuivre": ["HG.F", "USDCNY", "EURUSD"],
    "Aluminium": ["CL.F", "USDCNY", "EURUSD"],
    "Acier": ["CL.F", "USDCNY", "EURUSD"],
    "Semi-conducteurs": ["USDCNY", "EURUSD", "HG.F"],
    "RAM": ["USDCNY", "EURUSD", "HG.F"],
    "PCB": ["USDCNY", "EURUSD", "HG.F"],
    "Terres rares": ["USDCNY", "EURUSD"],
    "Lithium": ["USDCNY", "EURUSD"],
    "Cobalt": ["USDCNY", "EURUSD"],
    "Nickel": ["USDCNY", "EURUSD"],
    "Engrais NPK": ["CL.F", "ZW.F", "EURUSD"],
    "Soja": ["ZW.F", "EURUSD"],
    "Ble dur": ["ZW.F", "EURUSD"],
    "Energie": ["CL.F", "EURUSD"],
    "Coton": ["EURUSD", "USDCNY"],
    "Polyester": ["CL.F", "USDCNY"],
}


SECTOR_MARKET_MAP = {
    "Electronique": ["USDCNY", "EURUSD", "HG.F"],
    "Automobile": ["USDCNY", "EURUSD", "CL.F", "HG.F"],
    "Agroalimentaire": ["ZW.F", "CL.F", "EURUSD"],
    "Industrie manufacturiere": ["HG.F", "CL.F", "EURUSD"],
    "Construction": ["HG.F", "CL.F", "EURUSD"],
    "Textile": ["EURUSD", "USDCNY", "CL.F"],
}


def relevant_market_symbols(payload):
    symbols = set()
    for material in payload.get("materials", []):
        symbols.update(MARKET_EXPOSURE_MAP.get(material, []))
    symbols.update(SECTOR_MARKET_MAP.get(payload.get("sector", ""), []))
    trade_profile = payload.get("trade_profile", "")
    if "Exportateur" in trade_profile or "exportateur" in trade_profile:
        symbols.update(["EURUSD", "USDCNY"])
    if "Importateur" in trade_profile or "importateur" in trade_profile:
        symbols.update(["EURUSD", "USDCNY"])
    return symbols


def contextual_market_pressure(base_pressure, payload, result, quotes):
    relevant_symbols = relevant_market_symbols(payload)
    relevant_quotes = [quote for quote in quotes if quote["symbol"].upper() in relevant_symbols]
    quote_pressure = sum(min(abs(quote.get("change_pct", 0)) * 8, 16) for quote in relevant_quotes)
    risk_pressure = result.dimensions["Prix et devise"] * 0.14 + result.dimensions["Reglementaire"] * 0.10
    return min(100, int(round(base_pressure * 0.45 + quote_pressure + risk_pressure)))


def market_context_sentence(payload, result, relevant_quotes, contextual_pressure):
    materials = ", ".join(payload.get("materials", []))
    leader = max(result.dimensions.items(), key=lambda item: item[1])
    supplier_country = country_label_from_code(payload.get("supplier_country", ""))
    destination_country = country_label_from_code(payload.get("destination_country", ""))
    if relevant_quotes:
        move = max(relevant_quotes, key=lambda quote: abs(quote.get("change_pct", 0)))
        market_part = f"Le signal marche le plus sensible pour ce scenario est {move['label']} ({move['change_pct']:+.2f}%)."
    else:
        market_part = "Aucun signal de prix public directement relie aux flux selectionnes n'est disponible dans la veille actuelle."
    return (
        f"Contexte actif: {payload.get('trade_profile', 'Profil international')} | {payload.get('sector', 'Secteur')} | "
        f"{supplier_country} vers {destination_country} | {materials}. "
        f"Pression contextualisee: {contextual_pressure}/100. {market_part} "
        f"La dimension dominante reste {leader[0].lower()} ({leader[1]}/100), ce qui oriente la lecture du score, du radar, de la matrice et des actions."
    )


def dimension_detail_chart(result, key):
    dimensions = list(result.dimensions.keys())
    values = [result.dimensions[name] for name in dimensions]
    fig = go.Figure(
        go.Bar(
            x=values,
            y=dimensions,
            orientation="h",
            marker_color=[stat_color(value) for value in values],
            hovertemplate="%{y}: %{x}/100<extra></extra>",
        )
    )
    fig.update_layout(
        height=285,
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#f8fafc"),
        xaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,.09)"),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=20, r=20, t=10, b=20),
    )
    st.plotly_chart(fig, key=key, config={"displayModeBar": False, "responsive": True})


def score_gauge(result, key):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=result.global_score,
            number={"suffix": "/100"},
            delta={"reference": result.target_score, "relative": False, "valueformat": ".0f"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": level_color(result.global_score)},
                "steps": [
                    {"range": [0, 35], "color": "rgba(34,197,94,.25)"},
                    {"range": [35, 55], "color": "rgba(245,185,66,.22)"},
                    {"range": [55, 75], "color": "rgba(249,115,22,.22)"},
                    {"range": [75, 100], "color": "rgba(239,68,68,.25)"},
                ],
                "threshold": {"line": {"color": "#22c55e", "width": 4}, "value": result.target_score},
            },
        )
    )
    fig.update_layout(
        height=270,
        paper_bgcolor="#111827",
        font=dict(color="#f8fafc"),
        margin=dict(l=20, r=20, t=20, b=15),
    )
    st.plotly_chart(fig, key=key, config={"displayModeBar": False, "responsive": True})


def render_decision_scorecard(payload, result):
    st.markdown(
        f"""
        <div class="summary-box">
            <b>Lecture decisionnelle.</b> {esc(result.executive_summary)}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="context-band">
            <span class="pill">{esc(payload.get('trade_profile', 'Profil international'))}</span>
            <span class="pill">{esc(payload.get('sector', 'Secteur'))}</span>
            <span class="pill">{esc(', '.join(payload.get('materials', [])))}</span>
            <span class="pill">Niveau {esc(result.level)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([.95, 1.2])
    with left:
        score_gauge(result, key="active_score_gauge")
    with right:
        render_metrics(result)
        st.markdown(
            f"""
            <div class="decision-grid">
                <div class="decision-tile"><div class="metric-label">Decision</div><strong>{esc(result.level)}</strong><div class="small-muted">Priorite de pilotage du scenario actif.</div></div>
                <div class="decision-tile"><div class="metric-label">Reduction possible</div><strong>{result.score_reduction} pts</strong><div class="small-muted">Ecart entre score actuel et score cible.</div></div>
                <div class="decision-tile"><div class="metric-label">Cout residuel</div><strong>{esc(money(result.residual_cost))}</strong><div class="small-muted">Apres actions prioritaires.</div></div>
                <div class="decision-tile"><div class="metric-label">Actions</div><strong>{len(result.mitigation)}</strong><div class="small-muted">Leviers proposes par le moteur.</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    detail_col, chart_col = st.columns([.9, 1.25])
    with detail_col:
        selected_dimension = st.selectbox(
            "Dimension a analyser",
            list(result.dimensions.keys()),
            index=0,
            key="active_dimension_focus",
        )
        st.metric(
            selected_dimension,
            f"{result.dimensions[selected_dimension]}/100",
            help=DIMENSION_LABELS.get(selected_dimension, ""),
        )
        st.write(DIMENSION_LABELS.get(selected_dimension, ""))
        matching_causes = [
            cause for cause in result.root_causes
            if selected_dimension.lower().split()[0] in cause["title"].lower()
        ]
        if result.root_causes:
            cause = matching_causes[0] if matching_causes else result.root_causes[0]
            st.info(f"Cause prioritaire: {cause['title']} - {cause['detail']}")
    with chart_col:
        dimension_detail_chart(result, key="active_dimension_bars")


@st.cache_data(ttl=900, show_spinner="Chargement des taux BCE...")
def cached_ecb_rates():
    return fetch_ecb_rates()


@st.cache_data(ttl=900, show_spinner="Chargement des cotations publiques...")
def cached_market_quotes():
    return fetch_market_quotes()


@st.cache_data(ttl=900, show_spinner="Chargement des alertes GDELT...")
def cached_gdelt_alerts():
    return fetch_gdelt_alerts()


@st.cache_data(ttl=3600, show_spinner="Chargement des donnees macro publiques...")
def cached_world_bank_context(supplier_country, destination_country):
    return fetch_world_bank_context(supplier_country, destination_country)


def safe_market_load(label, loader):
    try:
        return loader(), None
    except Exception as exc:
        return None, f"{label}: {exc}"


def pressure_label(score):
    if score >= 65:
        return "Elevee"
    if score >= 35:
        return "Surveillance"
    return "Calme"


def quote_signal(change_pct):
    if change_pct >= 1:
        return "Hausse"
    if change_pct <= -1:
        return "Baisse"
    return "Stable"


def render_market_brief(pressure, quotes, news, rates_payload, payload=None, result=None):
    top_moves = sorted(quotes, key=lambda quote: abs(quote.get("change_pct", 0)), reverse=True)[:3]
    eur_usd = (rates_payload.get("rates") or {}).get("USD")
    brief_parts = [
        f"Pression marche: {pressure_label(pressure).lower()} ({pressure}/100).",
        f"{len(quotes)} indicateurs prix/devise charges.",
        f"{len(news)} alertes presse detectees.",
    ]
    if top_moves:
        leader = top_moves[0]
        brief_parts.append(f"Mouvement principal: {leader['label']} {leader['change_pct']:+.2f}%.")
    if eur_usd:
        brief_parts.append(f"EUR/USD BCE: {eur_usd:.4f}.")
    if payload and result:
        relevant_quotes = [quote for quote in quotes if quote["symbol"].upper() in relevant_market_symbols(payload)]
        contextual_pressure = contextual_market_pressure(pressure, payload, result, quotes)
        brief_parts.append(market_context_sentence(payload, result, relevant_quotes, contextual_pressure))

    st.markdown(
        f"""
        <div class="summary-box">
            <b>Lecture marche.</b> {" ".join(esc(part) for part in brief_parts)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if top_moves:
        st.markdown("#### Mouvements prioritaires")
        move_cols = st.columns(len(top_moves))
        for idx, quote in enumerate(top_moves):
            move_cols[idx].metric(
                quote["label"],
                f"{quote['close']:.4f}" if quote["close"] < 100 else f"{quote['close']:.2f}",
                f"{quote['change_pct']:+.2f}%",
            )


def render_market_segments(quotes, rates_payload):
    segments = [
        ("Energie", [q for q in quotes if q["type"] == "Energie"]),
        ("Metaux", [q for q in quotes if q["type"] == "Metaux"]),
        ("Agricole", [q for q in quotes if q["type"] == "Agricole"]),
        ("Devises", [q for q in quotes if q["type"] == "Devise"]),
    ]
    rows = []
    for label, items in segments:
        if items:
            max_move = max(abs(item["change_pct"]) for item in items)
            avg_move = sum(item["change_pct"] for item in items) / len(items)
            alert = "Elevee" if max_move >= 1.5 else "Surveillance" if max_move >= .75 else "Calme"
            rows.append({
                "Famille": label,
                "Alerte": alert,
                "Variation moyenne": f"{avg_move:+.2f}%",
                "Mouvement max": f"{max_move:.2f}%",
            })

    rates = rates_payload.get("rates", {})
    if rates.get("USD") and rates.get("CNY"):
        rows.append({
            "Famille": "EUR/CNY BCE",
            "Alerte": "Reference",
            "Variation moyenne": f"{rates['CNY']:.4f}",
            "Mouvement max": "Taux du jour",
        })

    st.markdown("#### Niveaux d'alerte par famille")
    if rows:
        st.dataframe(rows, width="stretch", hide_index=True)
    else:
        st.info("Les niveaux d'alerte seront calcules des que les cotations publiques seront disponibles.")


def render_market_alignment(payload, result, quotes, news, pressure):
    relevant_symbols = relevant_market_symbols(payload)
    relevant_quotes = [quote for quote in quotes if quote["symbol"].upper() in relevant_symbols]
    contextual_pressure = contextual_market_pressure(pressure, payload, result, quotes)
    top_dimension = max(result.dimensions.items(), key=lambda item: item[1])
    top_action = result.mitigation[0] if result.mitigation else None

    st.markdown("#### Alignement scenario actif")
    st.caption("Cette lecture relie les signaux publics au profil entreprise, puis aux vues Score, Radar, Matrice et Mitigation.")
    st.markdown(
        f"""
        <div class="decision-grid">
            <div class="decision-tile"><div class="metric-label">Score</div><strong>{result.global_score}/100</strong><div class="small-muted">Pression marche contextualisee: {contextual_pressure}/100.</div></div>
            <div class="decision-tile"><div class="metric-label">Radar</div><strong>{esc(top_dimension[0])}</strong><div class="small-muted">Dimension dominante: {top_dimension[1]}/100.</div></div>
            <div class="decision-tile"><div class="metric-label">Matrice</div><strong>P{result.probability} / I{result.impact}</strong><div class="small-muted">Position du scenario actif.</div></div>
            <div class="decision-tile"><div class="metric-label">Mitigation</div><strong>{esc(top_action['title'] if top_action else 'A definir')}</strong><div class="small-muted">{esc(top_action['horizon'] if top_action else 'Aucune action prioritaire')}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if relevant_quotes:
        rows = [{
            "Signal pertinent": quote["label"],
            "Type": quote["type"],
            "Variation": f"{quote['change_pct']:+.2f}%",
            "Lien scenario": "Flux critique / devise / secteur",
        } for quote in relevant_quotes]
        st.dataframe(rows, width="stretch", hide_index=True)
    else:
        st.info("Aucun indicateur public de la watchlist ne correspond directement aux flux du scenario actif.")

    if news:
        keywords = [payload.get("sector", ""), payload.get("trade_profile", "")] + payload.get("materials", [])
        filtered_news = [
            article for article in news
            if any(keyword and keyword.lower().split()[0] in article["title"].lower() for keyword in keywords)
        ][:3]
        if filtered_news:
            st.markdown("#### Alertes les plus proches du contexte")
            for article in filtered_news:
                st.write(f"**{article['title']}**")
                st.caption(f"{article['domain']} | {article['date']}")


def macro_alert_level(indicator):
    label = indicator.get("label", "")
    value = indicator.get("value", 0)
    if label == "Inflation":
        return "Elevee" if value >= 8 else "Surveillance" if value >= 4 else "Calme"
    if label == "Croissance PIB":
        return "Elevee" if value <= -1 else "Surveillance" if value <= 1 else "Calme"
    if label == "Commerce / PIB":
        return "Expose" if value >= 80 else "Ouvert" if value >= 40 else "Domestique"
    return "Reference"


def format_macro_value(indicator):
    value = indicator.get("value", 0)
    label = indicator.get("label", "")
    if label in ("Export marchandises", "Import marchandises"):
        if abs(value) >= 1_000_000_000_000:
            return f"{value / 1_000_000_000_000:.1f} T USD"
        return f"{value / 1_000_000_000:.1f} Md USD"
    return f"{value:.1f}%"


def render_macro_context(macro_payload, payload, result):
    countries = (macro_payload or {}).get("countries", [])
    st.markdown("#### Contexte macro pays")
    st.caption("Source publique World Bank, utilisee pour relier le scenario au pays fournisseur et au marche client prioritaire.")

    if not countries:
        st.info("Aucune donnee macro publique disponible pour les pays du scenario actif.")
        return

    rows = []
    for country in countries:
        for indicator in country.get("indicators", []):
            rows.append({
                "Role": country.get("role", ""),
                "Pays": country.get("country", country.get("country_code", "")),
                "Indicateur": indicator["label"],
                "Valeur": format_macro_value(indicator),
                "Annee": indicator.get("date", ""),
                "Lecture": macro_alert_level(indicator),
                "Source": "World Bank",
            })

    if rows:
        st.dataframe(rows, width="stretch", hide_index=True)

    inflation_values = [
        indicator["value"]
        for country in countries
        for indicator in country.get("indicators", [])
        if indicator["label"] == "Inflation"
    ]
    trade_values = [
        indicator["value"]
        for country in countries
        for indicator in country.get("indicators", [])
        if indicator["label"] == "Commerce / PIB"
    ]
    macro_pressure = 0
    if inflation_values:
        macro_pressure += min(max(inflation_values) * 3, 30)
    if trade_values:
        macro_pressure += min(max(trade_values) * 0.20, 20)
    macro_pressure += result.dimensions["Prix et devise"] * 0.12 + result.dimensions["Reglementaire"] * 0.08
    macro_pressure = min(100, int(round(macro_pressure)))

    st.markdown(
        f"""
        <div class="summary-box">
            <b>Lecture macro.</b> Pression macro contextualisee: {macro_pressure}/100.
            Le couple {esc(country_label_from_code(payload.get('supplier_country', '')))} /
            {esc(country_label_from_code(payload.get('destination_country', '')))} est rapproche du score
            {result.global_score}/100, de la dimension prix-devise ({result.dimensions['Prix et devise']}/100)
            et de la dimension reglementaire ({result.dimensions['Reglementaire']}/100).
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_market_dashboard(payload, result):
    col_title, col_action = st.columns([1, .25])
    with col_title:
        st.markdown("### Dashboard marche public")
        st.caption("Donnees publiques chargees a l'ouverture, sans cle API. Les sources et dates sont affichees pour chaque bloc.")
    with col_action:
        if st.button("Actualiser", width="stretch"):
            cached_ecb_rates.clear()
            cached_market_quotes.clear()
            cached_gdelt_alerts.clear()
            cached_world_bank_context.clear()
            st.rerun()

    ecb, ecb_error = safe_market_load("BCE", cached_ecb_rates)
    quotes_payload, quotes_error = safe_market_load("Stooq", cached_market_quotes)
    news_payload, news_error = safe_market_load("GDELT / Google News", cached_gdelt_alerts)
    macro_payload, macro_error = safe_market_load(
        "World Bank",
        lambda: cached_world_bank_context(
            payload.get("supplier_country", ""),
            payload.get("destination_country", ""),
        ),
    )
    snapshot = {
        "ecb": ecb,
        "quotes": quotes_payload,
        "news": news_payload,
        "macro": macro_payload,
        "errors": [
            {"source": "ecb", "error": ecb_error} if ecb_error else None,
            {"source": "quotes", "error": quotes_error} if quotes_error else None,
            {"source": "news", "error": news_error} if news_error else None,
            {"source": "macro", "error": macro_error} if macro_error else None,
        ],
    }
    snapshot["errors"] = [error for error in snapshot["errors"] if error]
    pressure = market_pressure_score(snapshot)
    quotes = (quotes_payload or {}).get("quotes", [])
    quote_errors = (quotes_payload or {}).get("errors", [])
    news = (news_payload or {}).get("articles", [])
    rates_payload = ecb or {}

    metric_cols = st.columns(4)
    metric_cols[0].metric("Pression marche", f"{pressure}/100")
    metric_cols[1].metric("Cotations chargees", len(quotes))
    metric_cols[2].metric("Alertes presse 24h", len(news))
    metric_cols[3].metric("Date BCE", rates_payload.get("date", "N/D"))

    if snapshot.get("errors"):
        for error in snapshot["errors"]:
            st.warning(f"Source indisponible: {error['source']} - {error['error']}")
    if quote_errors:
        with st.expander("Details des cotations indisponibles"):
            for error in quote_errors:
                st.write(f"{error['symbol']}: {error['error']}")

    render_market_brief(pressure, quotes, news, rates_payload, payload, result)
    render_market_alignment(payload, result, quotes, news, pressure)
    render_macro_context(macro_payload, payload, result)
    render_market_segments(quotes, rates_payload)

    st.markdown("#### Prix, devises et matieres")
    if quotes:
        quote_rows = []
        for quote in quotes:
            quote_rows.append({
                "Indicateur": quote["label"],
                "Type": quote["type"],
                "Dernier": round(quote["close"], 4),
                "Variation jour": f"{quote['change_pct']:+.2f}%",
                "Date": quote["date"],
                "Heure": quote["time"],
                "Source": "Stooq",
            })
        st.dataframe(quote_rows, width="stretch", hide_index=True)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=[quote["label"] for quote in quotes],
                y=[quote["change_pct"] for quote in quotes],
                marker_color=["#ef4444" if quote["change_pct"] > 0 else "#22c55e" for quote in quotes],
                hovertemplate="%{x}<br>Variation: %{y:.2f}%<extra></extra>",
            )
        )
        fig.update_layout(
            height=320,
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font=dict(color="#f8fafc"),
            yaxis=dict(title="Variation intrajournaliere (%)", gridcolor="rgba(255,255,255,.09)"),
            xaxis=dict(gridcolor="rgba(255,255,255,.09)"),
            margin=dict(l=30, r=20, t=20, b=40),
        )
        st.plotly_chart(fig, key="market_quotes_bar", config={"displayModeBar": False, "responsive": True})
    else:
        st.info("Aucune cotation marche disponible pour le moment.")

    st.markdown("#### Devises BCE")
    rates = rates_payload.get("rates", {})
    if rates:
        fx_cols = st.columns(5)
        for idx, currency in enumerate(["USD", "CNY", "GBP", "CHF", "JPY"]):
            rate = rates.get(currency)
            if rate:
                fx_cols[idx].metric(f"EUR/{currency}", f"{rate:.4f}" if rate < 100 else f"{rate:.2f}")
    else:
        st.info("Les taux BCE ne sont pas disponibles pour le moment.")

    st.markdown("#### Alertes commerce international")
    news_source = (news_payload or {}).get("source", "GDELT Project")
    st.caption(f"Source active: {news_source}. GDELT est essaye en priorite, Google News RSS prend le relais si GDELT est lent.")

    if news:
        for article in news:
            with st.container(border=True):
                st.markdown(f"**{article['title']}**")
                st.caption(f"{article['domain']} | {article['country']} | {article['language']} | {article['date']}")
                if article["url"]:
                    st.link_button("Ouvrir la source", article["url"])
    else:
        st.info("Aucune alerte publique disponible sur la fenetre 24h.")

    st.markdown("#### Sources publiques")
    st.markdown(
        "- [Banque centrale europeenne - taux de reference](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)\n"
        "- [Stooq - cotations publiques](https://stooq.com)\n"
        "- [World Bank API - indicateurs pays](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392)\n"
        "- [GDELT Project - actualites mondiales](https://www.gdeltproject.org)\n"
        "- [Google News RSS - relais public si GDELT est lent](https://news.google.com)"
    )


def render_context_banner(payload, result, label):
    st.markdown(
        f"""
        <div class="summary-box">
            <b>{esc(label)}.</b> Scenario actif: {esc(payload.get('scenario_name', 'Scenario'))} ·
            {esc(payload.get('trade_profile', 'Profil international'))} · {esc(payload.get('sector', 'Secteur'))}.
            Score {result.global_score}/100, probabilite {result.probability}/100, impact {result.impact}/100.
        </div>
        """,
        unsafe_allow_html=True,
    )


def radar_chart(results, selected_names, key):
    categories = ["Approvisionnement", "Marches export", "Logistique", "Reglementaire", "Prix et devise", "Resilience interne", "Impact"]
    fig = go.Figure()
    for name in selected_names:
        result = results[name]
        values = [result.dimensions.get(cat, result.impact) for cat in categories]
        values.append(values[0])
        theta = categories + [categories[0]]
        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=theta,
                fill="toself",
                name=name,
            )
        )
    fig.update_layout(
        height=455,
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#f8fafc"),
        polar=dict(
            bgcolor="#111827",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,.14)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,.12)"),
        ),
        legend=dict(orientation="h"),
        margin=dict(l=40, r=40, t=30, b=30),
    )
    st.plotly_chart(
        fig,
        key=key,
        config={"displayModeBar": False, "responsive": True},
    )


def matrix_chart(results, selected_names, key):
    fig = go.Figure()
    zones = [
        (0, 35, 0, 35, "rgba(34,197,94,.15)"),
        (35, 75, 0, 55, "rgba(245,185,66,.14)"),
        (0, 55, 35, 75, "rgba(245,185,66,.14)"),
        (55, 100, 55, 100, "rgba(239,68,68,.16)"),
    ]
    for x0, x1, y0, y1, color in zones:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1, fillcolor=color, line_width=0)

    for name in selected_names:
        result = results[name]
        fig.add_trace(
            go.Scatter(
                x=[result.probability],
                y=[result.impact],
                mode="markers+text",
                text=[name],
                textposition="top center",
                marker=dict(size=18, color=level_color(result.global_score), line=dict(color="white", width=1)),
                hovertemplate=(
                    f"<b>{name}</b><br>"
                    "Probabilite: %{x}/100<br>"
                    "Impact: %{y}/100<br>"
                    f"Score: {result.global_score}/100<br>"
                    f"Cout: {money(result.non_action_cost)}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        height=460,
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#f8fafc"),
        xaxis=dict(title="Probabilite", range=[0, 100], gridcolor="rgba(255,255,255,.09)"),
        yaxis=dict(title="Impact", range=[0, 100], gridcolor="rgba(255,255,255,.09)"),
        showlegend=False,
        margin=dict(l=30, r=30, t=30, b=30),
    )
    st.plotly_chart(
        fig,
        key=key,
        config={"displayModeBar": False, "responsive": True},
    )


def comparison_table(results, selected_names):
    rows = []
    for name in selected_names:
        r = results[name]
        rows.append({
            "Scenario": name,
            "Score": r.global_score,
            "Cible": r.target_score,
            "Probabilite": r.probability,
            "Impact": r.impact,
            "Cout non-action": money(r.non_action_cost),
            "Gain potentiel": money(r.estimated_savings),
        })
    st.dataframe(rows, width="stretch", hide_index=True)


def render_comparison_legend():
    legend_rows = [
        {"Abreviation": "APP", "Libelle": "Approvisionnement", "Definition": "Dependance fournisseurs, concentration, stock tampon et substitution."},
        {"Abreviation": "EXP", "Libelle": "Marches export", "Definition": "Dependance aux pays clients, concentration aval et exposition commerciale."},
        {"Abreviation": "LOG", "Libelle": "Logistique", "Definition": "Routes, delais, diversite transport et capacite d'absorption."},
        {"Abreviation": "REG", "Libelle": "Reglementaire", "Definition": "Douane, sanctions, export control, licences et contraintes pays."},
        {"Abreviation": "FX", "Libelle": "Prix et devise", "Definition": "Volatilite matieres, energie, devise, paiement et couverture."},
        {"Abreviation": "RES", "Libelle": "Resilience interne", "Definition": "Maturite risque, veille, gouvernance et capacite de reaction."},
        {"Abreviation": "IMP", "Libelle": "Impact", "Definition": "Gravite economique et operationnelle potentielle du scenario."},
        {"Abreviation": "Cible", "Libelle": "Score cible", "Definition": "Score estime apres mise en oeuvre des actions prioritaires."},
    ]
    st.markdown("#### Legende")
    st.caption("Lecture des indicateurs: 0 = exposition faible, 100 = exposition critique. Plus le score est eleve, plus le risque est important.")
    st.dataframe(legend_rows, width="stretch", hide_index=True)


def render_methodology(payload, result):
    st.markdown("### Methodologie du diagnostic")
    st.markdown(
        f"""
        <div class="summary-box">
            <b>Lecture du modele.</b> Le score CriticalRisk transforme le questionnaire du scenario actif en six dimensions de risque,
            puis combine probabilite et impact pour produire un score global sur 100. Le resultat n'est pas une notation financiere:
            c'est une aide a la decision pour prioriser les actions de resilience import-export.
        </div>
        """,
        unsafe_allow_html=True,
    )

    score_rows = [
        {"Zone": "0-34", "Niveau": "Faible", "Lecture": "Risque contenu, veille active suffisante."},
        {"Zone": "35-54", "Niveau": "Modere", "Lecture": "Risque sous controle mais dependances a surveiller."},
        {"Zone": "55-74", "Niveau": "Eleve", "Lecture": "Plan de reduction du risque recommande."},
        {"Zone": "75-100", "Niveau": "Critique", "Lecture": "Risque de continuite d'activite, mitigation prioritaire."},
    ]
    st.markdown("#### Echelle de lecture")
    st.dataframe(score_rows, width="stretch", hide_index=True)

    dimension_rows = [
        {"Dimension": name, "Score actuel": f"{score}/100", "Ce que cela mesure": DIMENSION_LABELS[name]}
        for name, score in result.dimensions.items()
    ]
    st.markdown("#### Dimensions du modele")
    st.dataframe(dimension_rows, width="stretch", hide_index=True)

    st.markdown("#### Hypotheses et limites")
    hypothesis_rows = [
        {
            "Sujet": "Donnees declarees",
            "Position": "Le modele s'appuie sur les informations saisies par l'utilisateur et doit etre consolide avec donnees internes.",
        },
        {
            "Sujet": "Sources publiques",
            "Position": "Les donnees BCE, Stooq, World Bank, GDELT et Google News donnent un contexte marche, pas une preuve exhaustive.",
        },
        {
            "Sujet": "Score",
            "Position": "Le score sert a prioriser les decisions; il ne remplace pas un audit juridique, douanier, assurantiel ou financier.",
        },
        {
            "Sujet": "Comparaison scenarios",
            "Position": "Les scenarios sont comparables si les hypotheses de perimetre, volumes, pays et flux restent coherentes.",
        },
    ]
    st.dataframe(hypothesis_rows, width="stretch", hide_index=True)

    st.markdown("#### Feuille de route cabinet")
    roadmap_rows = [
        {"Horizon": "0-30 jours", "Objectif": "Verifier les donnees critiques", "Livrable": "Liste fournisseurs, pays, flux, incoterms, volumes et devises."},
        {"Horizon": "30-60 jours", "Objectif": "Reduire les dependances prioritaires", "Livrable": "Plan alternatives fournisseurs, clients, routes et clauses contractuelles."},
        {"Horizon": "60-90 jours", "Objectif": "Installer le pilotage", "Livrable": "Comite risque mensuel, seuils d'alerte et tableau de bord marche."},
        {"Horizon": "90 jours et plus", "Objectif": "Industrialiser la resilience", "Livrable": "Stress tests trimestriels, reporting direction et mise a jour du score."},
    ]
    st.dataframe(roadmap_rows, width="stretch", hide_index=True)

    st.caption(
        f"Scenario actif: {payload.get('scenario_name', 'Scenario')} | "
        f"{payload.get('trade_profile', 'Profil international')} | "
        f"{payload.get('sector', 'Secteur')} | Score {result.global_score}/100."
    )


def render_causes(result):
    if not result.root_causes:
        st.info("Aucune cause prioritaire identifiee pour ce scenario.")
        return

    cols = st.columns(min(3, len(result.root_causes)))
    for idx, cause in enumerate(result.root_causes):
        with cols[idx % len(cols)]:
            with st.container(border=True):
                st.caption(f"Cause | {cause['severity']}/100")
                st.markdown(f"**{cause['title']}**")
                st.progress(cause["severity"] / 100)
                st.write(cause["detail"])


def render_actions(result):
    for action in result.mitigation:
        st.markdown(
            f"""
            <div class="action-card" style="margin-bottom:.65rem">
                <div class="action-meta">{esc(action['priority'])} · {esc(action['horizon'])}</div>
                <div class="action-title">{esc(action['title'])}</div>
                <div class="small-muted">{esc(action['detail'])}</div>
                <div style="margin-top:.65rem;display:flex;gap:.45rem;flex-wrap:wrap">
                    <span class="pill">KPI: {esc(action['kpi'])}</span>
                    <span class="pill">Effort: {esc(action['effort'])}</span>
                    <span class="pill">Impact: {esc(action['impact'])}</span>
                    <span class="pill">-{action['score_effect']} pts</span>
                    <span class="pill">Valeur: {money(action['value_eur'])}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_scenarios(result):
    for scenario in result.scenario_impacts:
        color = level_color(scenario["impact_score"])
        st.markdown(
            f"""
            <div class="panel" style="margin-bottom:.65rem">
                <div style="display:flex;justify-content:space-between;gap:1rem;align-items:flex-start">
                    <div>
                        <div class="action-title">{esc(scenario['name'])}</div>
                        <div class="small-muted">{esc(scenario['description'])}</div>
                    </div>
                    <div style="text-align:right;min-width:150px">
                        <div style="color:{color};font-weight:950;font-size:1.35rem">{scenario['impact_score']}/100</div>
                        <div class="small-muted">{money(scenario['estimated_cost'])}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_report(active_name, payload, result):
    report_inputs = deepcopy(payload)
    report_inputs.pop("company", None)
    text_report = build_text_report(payload.get("company", ""), report_inputs, result)
    st.text_area("Apercu du rapport", text_report, height=360)
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Telecharger le rapport texte",
            data=text_report,
            file_name=f"criticalrisk_{active_name}_{date.today().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            width="stretch",
        )
    with col2:
        pdf = build_pdf(payload.get("company", ""), report_inputs, result)
        if pdf:
            st.download_button(
                "Telecharger le rapport PDF",
                data=pdf,
                file_name=f"criticalrisk_{active_name}_{date.today().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                width="stretch",
            )
        else:
            st.info("Installez reportlab pour activer l'export PDF.")


def main():
    init_state()
    render_scenario_sidebar()
    render_header()

    payload = active_payload()
    edited_payload = scenario_editor(payload)
    preview_result = calculate_risk(edited_payload)
    saved_results = calculate_all()
    active_name = st.session_state.active_scenario
    active_result = saved_results[active_name]

    st.divider()
    st.markdown("### Carte de score du scenario actif")
    render_decision_scorecard(edited_payload, preview_result)

    st.divider()
    selected_names = st.multiselect(
        "Scenarios a comparer",
        list(st.session_state.scenarios.keys()),
        default=list(st.session_state.scenarios.keys()),
    )
    if not selected_names:
        selected_names = [active_name]

    tab_market, tab_score, tab_radar, tab_matrix, tab_actions, tab_method, tab_report = st.tabs(
        ["Dashboard marche", "Score", "Radar", "Matrice", "Mitigation", "Methodologie", "Rapport PDF"]
    )

    with tab_market:
        render_market_dashboard(edited_payload, preview_result)

    with tab_score:
        render_context_banner(edited_payload, preview_result, "Lecture score")
        st.markdown("### Comparaison des scenarios")
        cols = st.columns(min(3, len(selected_names)))
        for idx, name in enumerate(selected_names):
            with cols[idx % len(cols)]:
                render_player_card(name, saved_results[name], compact=True)
        st.markdown("### Tableau comparatif")
        comparison_table(saved_results, selected_names)
        render_comparison_legend()

    with tab_radar:
        render_context_banner(edited_payload, preview_result, "Lecture radar")
        st.markdown("### Radar des indicateurs risque")
        radar_chart(saved_results, selected_names, key="radar_compare")

    with tab_matrix:
        render_context_banner(edited_payload, preview_result, "Lecture matrice")
        st.markdown("### Matrice probabilite / impact")
        matrix_chart(saved_results, selected_names, key="matrix_compare")

    with tab_actions:
        render_context_banner(edited_payload, preview_result, "Lecture mitigation")
        st.markdown("### Pourquoi ce scenario est risque")
        render_causes(preview_result)
        st.markdown("### Actions recommandees")
        render_actions(preview_result)
        st.markdown("### Stress tests")
        render_scenarios(preview_result)

    with tab_method:
        render_context_banner(edited_payload, preview_result, "Cadre methodologique")
        render_methodology(edited_payload, preview_result)

    with tab_report:
        st.markdown("### Rapport du scenario actif enregistre")
        st.caption("Le rapport utilise la version enregistree du scenario actif. Cliquez sur Enregistrer si vous venez de modifier le questionnaire.")
        render_report(active_name, payload, active_result)


if __name__ == "__main__":
    main()
