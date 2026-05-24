import csv
import json
from datetime import datetime, timezone
from io import StringIO
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


ECB_DAILY_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
STOOQ_QUOTE_URL = "https://stooq.com/q/l/"
WORLD_BANK_URL = "https://api.worldbank.org/v2/country"

MARKET_WATCHLIST = [
    {"symbol": "EURUSD", "label": "EUR/USD", "type": "Devise"},
    {"symbol": "USDCNY", "label": "USD/CNY", "type": "Devise"},
    {"symbol": "XAUUSD", "label": "Or spot", "type": "Metaux"},
    {"symbol": "HG.F", "label": "Cuivre", "type": "Metaux"},
    {"symbol": "CL.F", "label": "Petrole brut", "type": "Energie"},
    {"symbol": "ZW.F", "label": "Ble", "type": "Agricole"},
]

RISK_NEWS_QUERY = "(supply chain OR export controls OR sanctions)"

WORLD_BANK_INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "Croissance PIB",
    "FP.CPI.TOTL.ZG": "Inflation",
    "NE.TRD.GNFS.ZS": "Commerce / PIB",
    "TX.VAL.MRCH.CD.WT": "Export marchandises",
    "TM.VAL.MRCH.CD.WT": "Import marchandises",
}


def _fetch_text(url, timeout=10):
    request = Request(url, headers={"User-Agent": "CriticalRiskIntelligence/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_ecb_rates():
    xml_text = _fetch_text(ECB_DAILY_URL)
    root = ET.fromstring(xml_text)
    namespace = {"fx": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}
    dated_cube = root.find(".//fx:Cube/fx:Cube", namespace)
    if dated_cube is None:
        raise ValueError("Format BCE inattendu")

    rates = {"EUR": 1.0}
    for cube in dated_cube.findall("fx:Cube", namespace):
        currency = cube.attrib.get("currency")
        rate = cube.attrib.get("rate")
        if currency and rate:
            rates[currency] = float(rate)

    return {
        "source": "Banque centrale europeenne",
        "url": ECB_DAILY_URL,
        "date": dated_cube.attrib.get("time", ""),
        "rates": rates,
    }


def fetch_stooq_quote(symbol):
    url = f"{STOOQ_QUOTE_URL}?s={quote(symbol.lower())}&f=sd2t2ohlcv&h&e=csv"
    text = _fetch_text(url)
    rows = list(csv.DictReader(StringIO(text)))
    if not rows:
        raise ValueError(f"Cotation indisponible pour {symbol}")

    row = rows[0]
    if row.get("Close") in ("", "N/D", None):
        raise ValueError(f"Cotation indisponible pour {symbol}")

    close = float(row["Close"])
    open_price = float(row["Open"]) if row.get("Open") not in ("", "N/D", None) else close
    change_pct = ((close - open_price) / open_price * 100) if open_price else 0
    return {
        "symbol": row.get("Symbol", symbol),
        "date": row.get("Date", ""),
        "time": row.get("Time", ""),
        "open": open_price,
        "high": float(row["High"]) if row.get("High") not in ("", "N/D", None) else close,
        "low": float(row["Low"]) if row.get("Low") not in ("", "N/D", None) else close,
        "close": close,
        "change_pct": change_pct,
        "url": url,
    }


def fetch_market_quotes():
    quotes = []
    errors = []
    for item in MARKET_WATCHLIST:
        try:
            quote_data = fetch_stooq_quote(item["symbol"])
            quotes.append({**item, **quote_data})
        except (ValueError, URLError, TimeoutError) as exc:
            errors.append({"symbol": item["symbol"], "error": str(exc)})
    return {
        "source": "Stooq",
        "url": "https://stooq.com",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "quotes": quotes,
        "errors": errors,
    }


def fetch_world_bank_country(country_code):
    code = (country_code or "").strip().upper()
    if not code:
        return None

    indicators = []
    errors = []
    for indicator, label in WORLD_BANK_INDICATORS.items():
        url = f"{WORLD_BANK_URL}/{quote(code)}/indicator/{indicator}?format=json&per_page=5"
        try:
            payload = json.loads(_fetch_text(url, timeout=6))
            rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
            latest = next((row for row in rows if row.get("value") is not None), None)
            if latest:
                indicators.append({
                    "code": indicator,
                    "label": label,
                    "value": float(latest["value"]),
                    "date": latest.get("date", ""),
                    "country": (latest.get("country") or {}).get("value", code),
                    "url": url,
                })
        except (ValueError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append({"indicator": indicator, "error": str(exc)})

    country_name = indicators[0]["country"] if indicators else code
    return {
        "source": "World Bank",
        "country_code": code,
        "country": country_name,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "indicators": indicators,
        "errors": errors,
    }


def fetch_world_bank_context(supplier_country="", destination_country=""):
    countries = []
    seen = set()
    for role, code in (("Pays fournisseur", supplier_country), ("Pays client", destination_country)):
        normalized = (code or "").strip().upper()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        country = fetch_world_bank_country(normalized)
        if country:
            country["role"] = role
            countries.append(country)

    return {
        "source": "World Bank",
        "url": "https://data.worldbank.org",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "countries": countries,
    }


def fetch_gdelt_alerts(max_records=5, timespan="24h"):
    query = quote(RISK_NEWS_QUERY)
    url = (
        f"{GDELT_DOC_URL}?query={query}"
        f"&mode=ArtList&format=json&maxrecords={max_records}&timespan={timespan}"
    )
    try:
        payload = json.loads(_fetch_text(url, timeout=2))
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        return fetch_google_news_alerts(max_records=max_records, fallback_reason=str(exc))

    articles = []
    for article in payload.get("articles", []):
        articles.append({
            "title": article.get("title", "Sans titre"),
            "domain": article.get("domain", ""),
            "country": article.get("sourcecountry", ""),
            "language": article.get("language", ""),
            "date": article.get("seendate", ""),
            "url": article.get("url", ""),
        })
    return {
        "source": "GDELT Project",
        "url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "articles": articles,
    }


def fetch_google_news_alerts(max_records=5, fallback_reason=""):
    query = quote("supply chain sanctions export controls when:1d")
    url = f"{GOOGLE_NEWS_RSS_URL}?q={query}&hl=en-US&gl=US&ceid=US:en"
    xml_text = _fetch_text(url, timeout=6)
    root = ET.fromstring(xml_text)
    articles = []

    for item in root.findall("./channel/item")[:max_records]:
        source = item.find("source")
        articles.append({
            "title": item.findtext("title", "Sans titre"),
            "domain": source.text if source is not None and source.text else "Google News",
            "country": "",
            "language": "English",
            "date": item.findtext("pubDate", ""),
            "url": item.findtext("link", ""),
        })

    return {
        "source": "Google News RSS",
        "url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "fallback_reason": fallback_reason,
        "articles": articles,
    }


def build_market_snapshot():
    snapshot = {
        "ecb": None,
        "quotes": None,
        "news": None,
        "macro": None,
        "errors": [],
    }
    for key, fetcher in (
        ("ecb", fetch_ecb_rates),
        ("quotes", fetch_market_quotes),
        ("news", fetch_gdelt_alerts),
    ):
        try:
            snapshot[key] = fetcher()
        except (ValueError, URLError, TimeoutError, json.JSONDecodeError, ET.ParseError) as exc:
            snapshot["errors"].append({"source": key, "error": str(exc)})
    return snapshot


def market_pressure_score(snapshot):
    score = 0
    quotes = (snapshot.get("quotes") or {}).get("quotes", [])
    for quote in quotes:
        if abs(quote.get("change_pct", 0)) >= 1:
            score += 8
        if quote.get("type") in ("Energie", "Metaux") and quote.get("change_pct", 0) >= 1.5:
            score += 8

    articles = (snapshot.get("news") or {}).get("articles", [])
    score += min(len(articles) * 3, 24)
    return min(score, 100)
