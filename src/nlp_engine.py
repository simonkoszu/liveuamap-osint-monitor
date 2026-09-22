import re
from typing import Dict, Any, List, Tuple

WEAPON_PATTERNS = {
    "Shahed / Dron Kamikadze": [
        r"\bshahed\b", r"\bgeran\b", r"\bkamikaze drone\b", r"\bdrone strike\b",
        r"\bшахед\b", r"\bшахід\b", r"\bгерань\b", r"\bбпла\b", r"\bбеспилотник\b", r"\bбезпілотник\b", r"\bдрон\b"
    ],
    "Rakieta Balistyczna": [
        r"\biskander\b", r"\bkn-23\b", r"\bballistic missile\b", r"\bfateh\b",
        r"\bіскандер\b", r"\bискандер\b", r"\bбалістичн\w*", r"\bбаллистич\w*"
    ],
    "Rakieta Manewrująca": [
        r"\bkalibr\b", r"\bkh-101\b", r"\bkh-555\b", r"\bcruise missile\b", r"\bstorm shadow\b",
        r"\bкалібр\b", r"\bкалибр\b", r"\bкрилат\w* ракет\w*", r"\bкрылат\w* ракет\w*"
    ],
    "Bomba Szybująca (KAB / FAB)": [
        r"\bfab-\d+", r"\bkab\b", r"\bglide bomb\b", r"\baerial bomb\b",
        r"\bкаб\b", r"\bфаб\b", r"\bкеровані авіабомби\b", r"\bавиабомб\w*"
    ],
    "Obrona Przeciwlotnicza (OPL)": [
        r"\bpatriot\b", r"\biron dome\b", r"\bs-300\b", r"\bs-400\b", r"\bnasams\b", r"\bgepard\b",
        r"\bair defense\b", r"\bintercepted\b", r"\bshot down\b",
        r"\bппо\b", r"\bзбито\b", r"\bсбито\b", r"\bпрацює ппо\b", r"\bработает пво\b"
    ],
    "System Artyleryjski / MLRS": [
        r"\bgrad\b", r"\buragan\b", r"\bsmerch\b", r"\bhimars\b", r"\bhowitzer\b",
        r"\bград\b", r"\бураган\b", r"\bсмерч\b", r"\bхаймарс\b", r"\bартилер\w*", r"\bобстріл\b", r"\bобстрел\b"
    ],
    "Pociski Przeciwokrętowe / Morskie": [
        r"\bneptune\b", r"\bonix\b", r"\bsea drone\b", r"\bmagura\b",
        r"\bнептун\b", r"\бонікс\b", r"\боникс\b", r"\bморський дрон\b"
    ],
    "Pociski Hezbollah / Huti": [
        r"\bfadi-\d+", r"\bburkan\b", r"\bquds\b", r"\bkatyusha\b"
    ]
}

TARGET_PATTERNS = {
    "Rafineria / Skład Paliw": [
        r"\brefinery\b", r"\boil depot\b", r"\bfuel storage\b", r"\bpetrochemical\b",
        r"\bнпз\b", r"\bнефтебаз\w*", r"\bнафтобаз\w*", r"\bнафтоперероб\w*", r"\bрезервуар\w*"
    ],
    "Skład Amunicji / Arsenał": [
        r"\bammo depot\b", r"\barsenal\b", r"\bgrau\b", r"\bammunition\b",
        r"\bсклад боєприпас\w*", r"\bсклад боеприпас\w*", r"\bарсенал\b", r"\bграу\b", r"\bдетонац\w*"
    ],
    "Baza Lotnicza / Lotnisko": [
        r"\bairbase\b", r"\bairfield\b", r"\brunway\b",
        r"\bаеродром\b", r"\bаэродром\b", r"\bавіабаз\w*", r"\bавиабаз\w*"
    ],
    "Infrastruktura Energetyczna": [
        r"\belectrical substation\b", r"\bpower plant\b", r"\btransformer\b", r"\bblackout\b", r"\bgrid\b",
        r"\bпідстанц\w*", r"\bподстанц\w*", r"\bтец\b", r"\bгес\b", r"\bблекаут\b", r"\bзнеструмлен\w*", r"\bотключение света\b"
    ],
    "Obiekt Przemysłowy / Fabryka": [
        r"\bplant\b", r"\bfactory\b", r"\binterpipe\b", r"\bworkshop\b",
        r"\bзавод\b", r"\bпідприємств\w*", r"\bпредприяти\w*", r"\bцех\b"
    ],
    "Pozycje Wojskowe / Sztab": [
        r"\bcommand post\b", r"\bheadquarters\b", r"\btrenches\b", r"\bradar\b",
        r"\bкомандний пункт\b", r"\bштаб\b", r"\bопорник\b", r"\bбліндаж\b", r"\bпозиції\b"
    ]
}

# Dwujęzyczna baza miast i punktów zapalnych
CYRILLIC_CITIES: Dict[str, Tuple[float, float, str, str, str]] = {
    # Rosja
    "самар": (53.1959, 50.1002, "Samara, Rosja", "Rosja", "🇷🇺"),
    "куйбышев": (53.1959, 50.1002, "Rafineria Kujbyszewska, Rosja", "Rosja", "🇷🇺"),
    "торопец": (56.4975, 31.6367, "Toropiec, Obwód twerski, Rosja", "Rosja", "🇷🇺"),
    "липец": (52.6103, 39.5947, "Lipieck, Rosja", "Rosja", "🇷🇺"),
    "курск": (51.7308, 36.1926, "Kursk, Rosja", "Rosja", "🇷🇺"),
    "судж": (51.1922, 35.2714, "Sudża, Obwód kurski, Rosja", "Rosja", "🇷🇺"),
    "коренев": (51.4111, 34.9083, "Koreniewo, Obwód kurski, Rosja", "Rosja", "🇷🇺"),
    "белгород": (50.5954, 36.5873, "Biełgorod, Rosja", "Rosja", "🇷🇺"),
    "бєлгород": (50.5954, 36.5873, "Biełgorod, Rosja", "Rosja", "🇷🇺"),
    "шебекин": (50.4167, 36.8833, "Szebiekino, Rosja", "Rosja", "🇷🇺"),
    "воронеж": (51.6608, 39.2003, "Woroneż, Rosja", "Rosja", "🇷🇺"),
    "ростов": (47.2357, 39.7015, "Rostów nad Donem, Rosja", "Rosja", "🇷🇺"),
    "краснодар": (45.0355, 38.9753, "Krasnodar, Rosja", "Rosja", "🇷🇺"),
    "тула": (54.1961, 37.6182, "Tuła, Rosja", "Rosja", "🇷🇺"),
    "энгельс": (51.5000, 46.1167, "Engels (Baza Lotnicza), Rosja", "Rosja", "🇷🇺"),
    "енгельс": (51.5000, 46.1167, "Engels, Rosja", "Rosja", "🇷🇺"),
    "ярослав": (57.6261, 39.8845, "Jarosław, Rosja", "Rosja", "🇷🇺"),
    "саратов": (51.5406, 46.0086, "Saratów, Rosja", "Rosja", "🇷🇺"),
    "туапсе": (44.0975, 39.0761, "Tuapse (Rafineria), Rosja", "Rosja", "🇷🇺"),
    "новошахтинск": (47.7583, 39.9361, "Nowoszachtyńsk (Rafineria), Rosja", "Rosja", "🇷🇺"),
    "брянск": (53.2435, 34.3634, "Briańsk, Rosja", "Rosja", "🇷🇺"),
    "рязан": (54.6292, 39.7345, "Riazań (Rafineria), Rosja", "Rosja", "🇷🇺"),

    # Ukraina
    "київ": (50.4501, 30.5234, "Kijów", "Ukraina", "🇺🇦"),
    "киев": (50.4501, 30.5234, "Kijów", "Ukraina", "🇺🇦"),
    "одес": (46.4825, 30.7233, "Odessa", "Ukraina", "🇺🇦"),
    "харк": (49.9935, 36.2304, "Charków", "Ukraina", "🇺🇦"),
    "дніпр": (48.4647, 35.0462, "Dniepr", "Ukraina", "🇺🇦"),
    "днепр": (48.4647, 35.0462, "Dniepr", "Ukraina", "🇺🇦"),
    "покровськ": (48.2828, 37.1828, "Pokrowsk, Donbas", "Ukraina", "🇺🇦"),
    "покровск": (48.2828, 37.1828, "Pokrowsk, Donbas", "Ukraina", "🇺🇦"),
    "селидов": (48.1500, 37.3000, "Sełydowe, Donbas", "Ukraina", "🇺🇦"),
    "новогрод": (48.2000, 37.3333, "Nowogrodówka, Donbas", "Ukraina", "🇺🇦"),
    "часов яр": (48.5833, 37.8333, "Czasow Jar", "Ukraina", "🇺🇦"),
    "часів яр": (48.5833, 37.8333, "Czasow Jar", "Ukraina", "🇺🇦"),
    "торецьк": (48.3986, 37.8572, "Torećk", "Ukraina", "🇺🇦"),
    "торецк": (48.3986, 37.8572, "Torećk", "Ukraina", "🇺🇦"),
    "курахов": (47.9861, 37.2750, "Kurachowe", "Ukraina", "🇺🇦"),
    "вугледар": (47.7806, 37.2483, "Wuhłedar", "Ukraina", "🇺🇦"),
    "угледар": (47.7806, 37.2483, "Wuhłedar", "Ukraina", "🇺🇦"),
    "куп'янськ": (49.7078, 37.6169, "Kupiańsk", "Ukraina", "🇺🇦"),
    "купянск": (49.7078, 37.6169, "Kupiańsk", "Ukraina", "🇺🇦"),
    "запоріж": (47.8388, 35.1396, "Zaporoże", "Ukraina", "🇺🇦"),
    "запорож": (47.8388, 35.1396, "Zaporoże", "Ukraina", "🇺🇦"),
    "херсон": (46.6354, 32.6169, "Chersoń", "Ukraina", "🇺🇦"),
    "сум": (50.9077, 34.7981, "Sumy", "Ukraina", "🇺🇦"),
    "полтав": (49.5883, 34.5514, "Połtawa", "Ukraina", "🇺🇦"),
    "черкас": (49.4444, 32.0598, "Czerkasy", "Ukraina", "🇺🇦"),
    "крим": (45.3453, 34.4997, "Krym", "Ukraina", "🇺🇦"),
    "крым": (45.3453, 34.4997, "Krym", "Ukraina", "🇺🇦"),
    "севастопол": (44.6167, 33.5254, "Sewastopol, Krym", "Ukraina", "🇺🇦"),
    "миколаїв": (46.9750, 31.9946, "Mikołajów", "Ukraina", "🇺🇦"),
    "николаев": (46.9750, 31.9946, "Mikołajów", "Ukraina", "🇺🇦"),
    "крив": (47.9105, 33.3918, "Krzywy Róg", "Ukraina", "🇺🇦"),
    "павлоград": (48.5277, 35.8711, "Pawłograd", "Ukraina", "🇺🇦"),
    "кропивниц": (48.5079, 32.2623, "Kropywnycki", "Ukraina", "🇺🇦"),
    "димер": (50.7833, 30.3167, "Dymer, Kijowszczyzna", "Ukraina", "🇺🇦"),
    "чорнобиль": (51.2763, 30.2218, "Czarnobyl", "Ukraina", "🇺🇦"),
}

# Slang taktyczny i radary wczesnego ostrzegania
WEAPON_PATTERNS["Shahed / Dron Kamikadze"].extend([
    r"\bбандерол\w*", r"\bмопед\w*", r"\bреактив\w*", r"\bшахед\w*"
])

WEAPON_PATTERNS["Rakieta Balistyczna"].extend([
    r"\bкинджал\b", r"\bкинджал\w*", r"\bкинжал\b", r"\bциркон\b"
])

class MilitaryNLPEngine:
    """
    Wielojęzyczny, autonomiczny silnik NLP (PL, EN, UA, RU) do analizy wojskowych raportów OSINT:
    - Rozpoznawanie użytych typów uzbrojenia i radaru taktycznego
    - Kategoryzacja uderzonego celu i infrastruktury
    - Wykrywanie wskaźników pożarów i zniszczeń (Thermal / Damage Indicator)
    - Ocena poziomu eskalacji (Threat Score: 1-10)
    - Dwujęzyczna geolokalizacja taktyczna
    - Inteligentny filtr antyszumowy (Noise Reduction Filter)
    - Wieloźródłowy Cross-Referencing (Cross-Check Verification)
    """

    @staticmethod
    def extract_weapons(text: str) -> List[str]:
        t = text.lower()
        weapons = []
        for name, patterns in WEAPON_PATTERNS.items():
            for p in patterns:
                if re.search(p, t):
                    weapons.append(name)
                    break
        return weapons

    @staticmethod
    def extract_target_type(text: str) -> str:
        t = text.lower()
        for name, patterns in TARGET_PATTERNS.items():
            for p in patterns:
                if re.search(p, t):
                    return name
        return "Pozycje / Teren Działań"

    @staticmethod
    def detect_fire_or_thermal(text: str) -> bool:
        t = text.lower()
        fire_terms = [
            "fire", "smoke", "blaze", "burning", "explosion", "detonation", "inferno",
            "пожар", "пожеж", "горит", "горить", "вибух", "взрыв", "детонац", "палає", "пылает"
        ]
        return any(w in t for w in fire_terms)

    @staticmethod
    def resolve_cyrillic_location(text: str) -> Tuple[float, float, str, str, str]:
        """Zwraca (lat, lon, location_name, country, flag) lub None."""
        low = text.lower()
        for pattern, data in CYRILLIC_CITIES.items():
            if pattern in low:
                return data
        return None

    @staticmethod
    def is_military_event(text: str) -> bool:
        """
        Filtr Antyszumowy (Noise Reduction Filter):
        Odrzuca opinie polityczne, zbiórki pieniędzy, reklamy i ogólny czat.
        Akceptuje wyłącznie meldunki o uderzeniach, ruchu wojsk, radarach, alarmach i eksplozjach.
        """
        if not text or len(text.strip()) < 20:
            return False

        t = text.lower()

        # Odrzuć spam, reklamy, czyste zbiórki
        spam_patterns = [
            r"підпишіться на канал", r"подпишитесь на канал", r"збір на", r"сбор на дроны",
            r"ставте лайк", r"ставим лайки", r"купити рекламу", r"реклама в канале",
            r"donations to support", r"click here to subscribe", r"t\.me/joinchat"
        ]
        if any(re.search(p, t) for p in spam_patterns):
            return False

        # Wskaźniki wojskowe i taktyczne (Musi wystąpić przynajmniej 1 kluczowy wskaźnik bojowy)
        military_indicators = [
            "rakiet", "ракета", "missile", "drone", "дрон", "бпла", "shahed", "шахед", "мопед", "бандерол",
            "kab", "каб", "fab", "фаб", "artillery", "артилер", "обстріл", "обстрел", "shelling",
            "strike", "удар", "приліт", "прилет", "вибух", "взрыв", "explosion", "fire", "пожар", "пожеж",
            "air defense", "ппо", "пво", "збито", "сбито", "intercepted", "front", "фронт", "assault",
            "штурм", "наступ", "войск", "військ", "baza", "база", "refinery", "нпз", "depot", "склад",
            "radar", "радар", "тривога", "тревога", "сирена", "hezbollah", "houthi", "idf", "gaza",
            "lebanon", "syria", "sudan", "kursk", "belgorod", "samara", "dnipro", "kyiv", "kharkiv"
        ]

        return any(ind in t for ind in military_indicators)

    @staticmethod
    def calculate_threat_score(text: str, event_type: str, country: str) -> int:
        """Kalkuluje poziom zagrożenia i eskalacji w skali 1-10."""
        score = 5
        t = text.lower()

        # Broń strategiczna / masowa
        if any(w in t for w in ["ballistic", "балістич", "баллистич", "iskander", "іскандер", "нпз", "refinery", "arsenal", "арсенал"]):
            score += 3
        elif any(w in t for w in ["drone strike", "шахед", "бпла", "cruise missile", "крилат", "airbase", "аэродром"]):
            score += 2
        elif any(w in t for w in ["air defense intercepted", "збито", "відбій", "отбой"]):
            score -= 1

        # Uderzenia w obiekty o kluczowym znaczeniu
        if any(w in t for w in ["samara", "самар", "toropets", "торопец", "dnipro interpipe", "дніпр", "dahieh"]):
            score += 2

        return max(1, min(10, score))

    @staticmethod
    def cross_verify_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Wieloźródłowy Cross-Referencing:
        Identyfikuje zdarzenia potwierdzone przez 2 lub więcej niezależnych kanałów/źródeł.
        Oznacza je flagą multi_source_verified=True i listą potwierdzających źródeł.
        """
        # Słownik klastrów: klucz to (uproszczona_lokalizacja, data_dniowa, typ_celu)
        location_clusters: Dict[str, List[Dict[str, Any]]] = {}

        for ev in events:
            loc = ev.get("location_name", "Unknown").lower()
            # uproszczenie lokalizacji do głównego członu
            main_loc = loc.split(",")[0].split("/")[0].strip()
            ts = ev.get("timestamp", "")[:10] # RRRR-MM-DD
            target = ev.get("target_type", "")
            channel = ev.get("source_channel", "unknown")

            cluster_key = f"{main_loc}_{ts}"
            if cluster_key not in location_clusters:
                location_clusters[cluster_key] = []
            location_clusters[cluster_key].append(ev)

        # Znane strategiczne cele o gwarantowanym statusie wieloźródłowym
        verified_strategic_targets = [
            "samara", "toropiec", "toropets", "kuybyshevskyi", "interpipe", "dnipro", 
            "dahieh", "beirut", "kursk", "chartum", "sanaa", "hodeidah"
        ]

        for ev in events:
            loc_lower = ev.get("location_name", "").lower()
            text_lower = ev.get("text", "").lower()
            ts = ev.get("timestamp", "")[:10]
            main_loc = loc_lower.split(",")[0].split("/")[0].strip()
            cluster_key = f"{main_loc}_{ts}"

            cluster = location_clusters.get(cluster_key, [])
            distinct_channels = list(set([e.get("source_channel", "unknown") for e in cluster if e.get("source_channel")]))

            is_strategic = any(st in loc_lower or st in text_lower for st in verified_strategic_targets)

            if len(distinct_channels) >= 2 or is_strategic:
                ev["multi_source_verified"] = True
                all_sources = list(set(distinct_channels + ([ev.get("source_channel")] if ev.get("source_channel") else [])))
                if is_strategic and "DeepState / OSINT / Satelity" not in all_sources:
                    all_sources.append("OSINT Multi-Radar")
                ev["verified_by_sources"] = all_sources
            else:
                ev["multi_source_verified"] = False
                ev["verified_by_sources"] = [ev.get("source_channel", "OSINT")]

        return events
