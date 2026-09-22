"""
Moduł Tłumacza Wojskowego (Aegis Military Translator).
Tłumaczy tytuły i opisy zdarzeń wojennych z języka angielskiego, ukraińskiego i rosyjskiego na język polski.
Wykorzystuje bezpłatne API tłumaczeniowe z wbudowanym buforem (cache) oraz słownikiem terminologii wojskowej.
"""

import time
import json
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Any

# Słownik stałych wojskowych terminów (fallback i standaryzacja)
MILITARY_GLOSSARY = {
    r"\bMLRS\b": "wieloprowadnicowe wyrzutnie rakietowe (MLRS)",
    r"\bair defense\b": "obrona powietrzna",
    r"\bair raid alert\b": "alarm przeciwlotniczy",
    r"\bballistic missile\b": "rakieta balistyczna",
    r"\bcruise missile\b": "rakieta manewrująca",
    r"\bglide bomb\b": "bomba szybująca (KAB)",
    r"\bGeneral Staff of Armed Forces\b": "Sztab Generalny Sił Zbrojnych",
    r"\boil refinery\b": "rafineria ropy naftowej",
    r"\boil depot\b": "skład paliw",
    r"\bpower plant\b": "elektrownia",
    r"\binterception\b": "przechwycenie",
    r"\bcasualties\b": "ofiary",
}

_TRANSLATION_CACHE = {}

def translate_to_polish(text: str) -> str:
    """Tłumaczy pojedynczy ciąg znaków na język polski z obsługą cache."""
    if not text or not text.strip():
        return ""

    clean_text = text.strip()
    if clean_text in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[clean_text]

    # Jeśli tekst jest bardzo krótki lub zawiera głównie cyfry/symbole
    if len(clean_text) < 3:
        return clean_text

    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=pl&dt=t&q=" + urllib.parse.quote(clean_text)
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data and data[0]:
                translated = "".join([part[0] for part in data[0] if part and part[0]])
                _TRANSLATION_CACHE[clean_text] = translated
                return translated
    except Exception as e:
        # Fallback na słownik terminologii wojskowej
        translated = clean_text
        for pattern, replacement in MILITARY_GLOSSARY.items():
            translated = re.sub(pattern, replacement, translated, flags=re.IGNORECASE)
        _TRANSLATION_CACHE[clean_text] = translated
        return translated

    return clean_text

def translate_events_batch(events: List[Dict[str, Any]], max_to_translate: int = 150) -> int:
    """
    Tłumaczy zdarzenia w partii.
    Zapisuje przetłumaczone pola pod kluczami 'title_pl' oraz 'text_pl'.
    Zwraca liczbę nowo przetłumaczonych zdarzeń.
    """
    translated_count = 0
    print(f"[TRANSLATOR] Weryfikacja tłumaczeń polskich dla {len(events)} incydentów...")

    for ev in events:
        if translated_count >= max_to_translate:
            break

        orig_title = (ev.get("title") or "").strip()
        orig_text = (ev.get("text") or "").strip()

        needs_title = (not ev.get("title_pl") or ev.get("title_pl") == orig_title) and orig_title
        needs_text = (not ev.get("text_pl") or ev.get("text_pl") == orig_text) and orig_text

        if needs_title or needs_text:
            if needs_title:
                ev["title_pl"] = translate_to_polish(orig_title)
            if needs_text:
                ev["text_pl"] = translate_to_polish(orig_text)

            translated_count += 1
            if translated_count % 15 == 0:
                print(f"[TRANSLATOR] Przetłumaczono {translated_count} zdarzeń na j. polski...")
                time.sleep(0.15)  # Drobny odstęp, aby nie przekroczyć limitów API

    print(f"[TRANSLATOR] Zakończono: {translated_count} nowych zdarzeń przetłumaczonych na język polski.")
    return translated_count
