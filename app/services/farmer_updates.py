import json
import requests
from xml.etree import ElementTree

from ..extensions import get_redis
from ..state_data import STATE_AGRICULTURE_PORTALS, STATE_NAMES_HI

NEWS_FEED = "https://news.google.com/rss/search"
NEWS_CACHE_SECONDS = 900


def get_state_news(state, language="en"):
    """Return recent agriculture headlines matching a state from Google News RSS."""
    if not state:
        return []

    language = "hi" if language == "hi" else "en"
    cache_key = f"kisan:state-news:{language}:{state.casefold().replace(' ', '-')}"
    cache = get_redis()
    if cache:
        try:
            cached = cache.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

    locale = {"hl": "hi-IN" if language == "hi" else "en-IN",
              "gl": "IN", "ceid": "IN:hi" if language == "hi" else "IN:en",
              "q": f'agriculture farmers "{state}"'}
    try:
        response = requests.get(NEWS_FEED, params=locale, timeout=(3, 6),
                                headers={"User-Agent": "KisanBhai/1.0"})
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        news = []
        for item in root.findall("./channel/item")[:5]:
            source = item.findtext("source") or "News source"
            news.append({
                "title": item.findtext("title", "").strip(),
                "url": item.findtext("link", "").strip(),
                "source": source.strip(),
                "published": item.findtext("pubDate", "").strip(),
            })
        if cache:
            try:
                cache.setex(cache_key, NEWS_CACHE_SECONDS, json.dumps(news))
            except Exception:
                pass
        return news
    except (requests.RequestException, ElementTree.ParseError):
        return []


def state_scheme_links(state, language="en"):
    """Official scheme discovery and application portals for the selected state."""
    if language == "hi":
        state_label = STATE_NAMES_HI.get(state, state)
        return [
            {"title": "राज्य कृषि विभाग", "description": f"{state_label} के लिए आधिकारिक कृषि सेवाएँ और अपडेट।",
             "url": STATE_AGRICULTURE_PORTALS.get(state, "https://farmerconnect.apeda.gov.in/Home/UsefulLinks"),
             "kind": "state"},
            {"title": "अपने राज्य की योजनाएँ खोजें", "description": "राज्य चुनकर पात्रता और सरकारी योजना की जानकारी देखें।",
             "url": "https://www.myscheme.gov.in/find-scheme/screen-2", "kind": "finder"},
            {"title": "पीएम-किसान", "description": "लाभार्थी और किस्त की जानकारी के लिए आधिकारिक पोर्टल।",
             "url": "https://pmkisan.gov.in/", "kind": "central"},
            {"title": "प्रधानमंत्री फसल बीमा योजना", "description": "फसल बीमा पोर्टल; उपलब्धता और अधिसूचित फसलें राज्य व मौसम के अनुसार बदलती हैं।",
             "url": "https://pmfby.gov.in/", "kind": "central"},
        ]
    return [
        {"title": "State Agriculture Department", "description": f"Official agriculture services and updates for {state}.",
         "url": STATE_AGRICULTURE_PORTALS.get(state, "https://farmerconnect.apeda.gov.in/Home/UsefulLinks"),
         "kind": "state"},
        {"title": "Find schemes for your state", "description": "Use the Government of India scheme finder to select your state and check eligibility.",
         "url": "https://www.myscheme.gov.in/find-scheme/screen-2", "kind": "finder"},
        {"title": "PM-KISAN", "description": "Official portal for beneficiary and installment information.",
         "url": "https://pmkisan.gov.in/", "kind": "central"},
        {"title": "PM Fasal Bima Yojana", "description": "Official crop insurance portal; availability and notified crops vary by state and season.",
         "url": "https://pmfby.gov.in/", "kind": "central"},
    ]
