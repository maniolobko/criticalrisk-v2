from copy import deepcopy
from datetime import date
import html

import plotly.graph_objects as go
import streamlit as st

from data import MATERIAL_RISK, PERSONAS, SECTORS, TRADE_PROFILES
from market_data import fetch_ecb_rates, fetch_gdelt_alerts, fetch_market_quotes, market_pressure_score
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
        font-size:.72rem;
        font-weight:900;
        text-transform:uppercase;
    }
    .hero h1 { margin:.3rem 0 0; font-size:2rem; line-height:1.12; }
    .hero p { color:var(--muted); max-width:760px; margin:.65rem 0 0; line-height:1.55; }
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
    .stButton > button, .stDownloadButton > button {
        border-radius:8px !important;
        border:1px solid rgba(245,185,66,.4) !important;
        background:#f5b942 !important;
        color:#111827 !important;
        font-weight:900 !important;
    }
    @media (max-width: 900px) {
        .hero { display:block; }
        .metric-grid, .cause-grid { grid-template-columns:1fr; }
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
                <h1>Simulateur interactif de risques import-export.</h1>
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


@st.cache_data(ttl=900, show_spinner="Chargement des taux BCE...")
def cached_ecb_rates():
    return fetch_ecb_rates()


@st.cache_data(ttl=900, show_spinner="Chargement des cotations publiques...")
def cached_market_quotes():
    return fetch_market_quotes()


@st.cache_data(ttl=900, show_spinner="Chargement des alertes GDELT...")
def cached_gdelt_alerts():
    return fetch_gdelt_alerts()


def safe_market_load(label, loader):
    try:
        return loader(), None
    except Exception as exc:
        return None, f"{label}: {exc}"


def render_market_dashboard():
    col_title, col_action = st.columns([1, .25])
    with col_title:
        st.markdown("### Dashboard marche public")
        st.caption("Donnees publiques chargees a l'ouverture, sans cle API. Les sources et dates sont affichees pour chaque bloc.")
    with col_action:
        if st.button("Actualiser", width="stretch"):
            cached_ecb_rates.clear()
            cached_market_quotes.clear()
            cached_gdelt_alerts.clear()
            st.rerun()

    ecb, ecb_error = safe_market_load("BCE", cached_ecb_rates)
    quotes_payload, quotes_error = safe_market_load("Stooq", cached_market_quotes)
    news_payload, news_error = safe_market_load("GDELT / Google News", cached_gdelt_alerts)
    snapshot = {
        "ecb": ecb,
        "quotes": quotes_payload,
        "news": news_payload,
        "errors": [
            {"source": "ecb", "error": ecb_error} if ecb_error else None,
            {"source": "quotes", "error": quotes_error} if quotes_error else None,
            {"source": "news", "error": news_error} if news_error else None,
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
        "- [GDELT Project - actualites mondiales](https://www.gdeltproject.org)\n"
        "- [Google News RSS - relais public si GDELT est lent](https://news.google.com)"
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
            st.info("Installez fpdf2 pour activer l'export PDF.")


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
    c1, c2 = st.columns([.9, 1.3])
    with c1:
        render_player_card(edited_payload["scenario_name"], preview_result)
    with c2:
        st.markdown(
            f"""
            <div class="summary-box">
                <b>Synthese.</b> {esc(preview_result.executive_summary)}
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_metrics(preview_result)

    st.divider()
    selected_names = st.multiselect(
        "Scenarios a comparer",
        list(st.session_state.scenarios.keys()),
        default=list(st.session_state.scenarios.keys()),
    )
    if not selected_names:
        selected_names = [active_name]

    tab_market, tab_score, tab_radar, tab_matrix, tab_actions, tab_report = st.tabs(
        ["Dashboard marche", "Score", "Radar", "Matrice", "Mitigation", "Rapport PDF"]
    )

    with tab_market:
        render_market_dashboard()

    with tab_score:
        st.markdown("### Comparaison des scenarios")
        cols = st.columns(min(3, len(selected_names)))
        for idx, name in enumerate(selected_names):
            with cols[idx % len(cols)]:
                render_player_card(name, saved_results[name], compact=True)
        st.markdown("### Tableau comparatif")
        comparison_table(saved_results, selected_names)

    with tab_radar:
        st.markdown("### Radar des indicateurs risque")
        radar_chart(saved_results, selected_names, key="radar_compare")

    with tab_matrix:
        st.markdown("### Matrice probabilite / impact")
        matrix_chart(saved_results, selected_names, key="matrix_compare")

    with tab_actions:
        st.markdown("### Pourquoi ce scenario est risque")
        render_causes(preview_result)
        st.markdown("### Actions recommandees")
        render_actions(preview_result)
        st.markdown("### Stress tests")
        render_scenarios(preview_result)

    with tab_report:
        st.markdown("### Rapport du scenario actif enregistre")
        st.caption("Le rapport utilise la version enregistree du scenario actif. Cliquez sur Enregistrer si vous venez de modifier le questionnaire.")
        render_report(active_name, payload, active_result)


if __name__ == "__main__":
    main()
