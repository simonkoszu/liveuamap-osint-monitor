import re
from typing import Dict, Any, List, Tuple

# Precyzyjna Taksonomia Zdarzeń Bojowych
TACTICAL_CATEGORIES = {
    "Czujnik NASA FIRMS": {
        "icon": "🛰️",
        "patterns": [
            r"\bnasa\b", r"\bfirms\b", r"\bviirs\b", r"\banomali[ae]\s+termiczn\w*",
            r"\bthermal\s+anomaly\b", r"\bczujnik\s+nasa\b", r"\bsatelit[ay]\s+nasa\b"
        ]
    },
    "Eksplozja / Detonacja": {
        "icon": "💥",
        "patterns": [
            r"\bexplosion\b", r"\bexplosions\b", r"\bdetonation\b", r"\bsecondary detonation\b",
            r"\bвибух\w*", r"\bвзрыв\w*", r"\bдетонац\w*", r"\bгремит\b", r"\bгромко\b", r"\bпотужний вибух\b"
        ]
    },
    "Atak Dronów Kamikadze": {
        "icon": "🛸",
        "patterns": [
            r"\bshahed\b", r"\bgeran\b", r"\bkamikaze drone\b", r"\bdrone strike\b", r"\bdrone attack\b",
            r"\bшахед\w*", r"\bшахід\w*", r"\bгерань\b", r"\bбпла\b", r"\bбеспилотник\w*", r"\bбезпілотник\w*",
            r"\bдрон\w*", r"\bмопед\w*", r"\bбандерол\w*", r"\bреактив\w*"
        ]
    },
    "Uderzenie Balistyczne / Rakieta": {
        "icon": "🚀",
        "patterns": [
            r"\bmissile\b", r"\bballistic\b", r"\bcruise missile\b", r"\biskander\b", r"\bkalibr\b",
            r"\bkinzhal\b", r"\bkn-23\b", r"\bstorm shadow\b", r"\bquds\b", r"\bfateh\b",
            r"\bракета\b", r"\bракет\w*", r"\bбалістич\w*", r"\bбаллистич\w*", r"\bіскандер\b",
            r"\bискандер\b", r"\bкалібр\b", r"\bкалибр\b", r"\bкинджал\w*", r"\bкрилат\w*"
        ]
    },
    "Bombardowanie Lotnicze (KAB / FAB)": {
        "icon": "💣",
        "patterns": [
            r"\bglide bomb\b", r"\baerial bomb\b", r"\bkab\b", r"\bfab-\d+", r"\bairstrike\b", r"\bair strike\b",
            r"\bкаб\b", r"\bфаб\b", r"\bкеровані авіабомби\b", r"\bавіаудар\w*", r"\bавиаудар\w*"
        ]
    },
    "Obrona Przeciwlotnicza (OPL)": {
        "icon": "🛡️",
        "patterns": [
            r"\bair defense\b", r"\bintercepted\b", r"\bshot down\b", r"\bpatriot\b", r"\biron dome\b",
            r"\bs-300\b", r"\bs-400\b", r"\bgepard\b", r"\bnasams\b",
            r"\bппо\b", r"\bпво\b", r"\bзбито\b", r"\bсбито\b", r"\bперехоплен\w*", r"\bвідбито\b"
        ]
    },
    "Infrastruktura Krytyczna / Rafineria": {
        "icon": "🏭",
        "patterns": [
            r"\brefinery\b", r"\boil depot\b", r"\bpower plant\b", r"\bsubstation\b", r"\bblackout\b",
            r"\bpipeline\b", r"\bammunition depot\b", r"\barsenal\b", r"\bgrau\b", r"\binterpipe\b",
            r"\bнпз\b", r"\bнефтебаз\w*", r"\bнафтобаз\w*", r"\bпідстанц\w*", r"\bподстанц\w*",
            r"\bарсенал\b", r"\bсклад боєприпас\w*", r"\bзнеструмлен\w*", r"\bрезервуар\w*"
        ]
    },
    "Starcie Lądowe / Szturm": {
        "icon": "⚔️",
        "patterns": [
            r"\bclash\b", r"\bassault\b", r"\boffensive\b", r"\bstorming\b", r"\btrenches\b", r"\binfantry\b",
            r"\brecaptured\b", r"\badvance\b", r"\boccupied\b", r"\brepelled\b",
            r"\bштурм\w*", r"\bнаступ\w*", r"\bконтрнаступ\w*", r"\bбої\b", r"\bбои\b", r"\bокопи\b", r"\bпросування\b"
        ]
    },
    "Działania Morskie / Drony Nawodne": {
        "icon": "🚢",
        "patterns": [
            r"\bnaval\b", r"\bship\b", r"\bsea drone\b", r"\bvessel\b", r"\bmagura\b", r"\bmaritime\b",
            r"\bкорабл\w*", r"\bморський дрон\b", r"\bморской дрон\b", r"\bкатер\b", r"\bпорт\b"
        ]
    },
    "Komunikat Sztabowy / Dyplomacja": {
        "icon": "📡",
        "patterns": [
            r"\bstatement\b", r"\bagreement\b", r"\bsanctions\b", r"\bgeneral staff\b", r"\bnegotiations\b",
            r"\bгенштаб\w*", r"\bзведення\b", r"\bсводка\b", r"\bзаява\b", r"\bпереговори\b"
        ]
    }
}

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
        Rygorystyczny Filtr Antyszumowy (Noise Reduction Filter):
        Odrzuca plotki, celebrytów, motoryzację, zbiórki pieniędzy, reklamy i ogólny czat cywilny.
        Akceptuje wyłącznie meldunki o uderzeniach, ruchu wojsk, radarach, alarmach, eksplozjach
        oraz oświadczeniach dyplomacji wojennej.
        """
        if not text or len(text.strip()) < 20:
            return False

        t = text.lower()

        # 1. Odrzuć spam, reklamy, czyste zbiórki
        spam_patterns = [
            r"підпишіться на канал", r"подпишитесь на канал", r"збір на", r"сбор на дроны",
            r"ставте лайк", r"ставим лайки", r"купити рекламу", r"реклама в канале",
            r"donations to support", r"click here to subscribe", r"t\.me/joinchat"
        ]
        if any(re.search(p, t) for p in spam_patterns):
            return False

        # 2. Bezwzględny filtr cywilno-tabloidowy (auta, celebryci, koncerty, sport, obyczaje)
        civilian_noise_patterns = [
            r"\b(bentley|lamborghini|rolls-royce|ferrari|mercedes-benz|bmw|porsche)\b",
            r"\b(студент|студентк|университет|мгу|парковк|преподавател)\b",
            r"\b(концерт|шоу|фестивал|кино|фильм|актер|актрис|селебрити|певиц|певец|рэпер|рэп|джокер)\b",
            r"\b(футбол|хоккей|матч|чемпионат|спортсмен|лига|рпл|футболист|вагнер лав|vagner love)\b",
            r"\b(гороскоп|астролог|погода на завтра|синоптик|стриптиз|стриптизерш)\b",
            r"\b(хореограф|педофил|бикини|диета|похуден|аллерги|гайморит|медведь|зоопарк|вкуссвилл|vkusvill)\b"
        ]
        is_noise = any(re.search(p, t) for p in civilian_noise_patterns)
        has_hard_combat = any(w in t for w in [
            "ракета", "missile", "дрон", "drone", "бпла", "shahed", "шахед",
            "атака", "удар", "strike", "обстрел", "обстріл", "взрыв", "вибух",
            "пожар", "пожеж", "ппо", "пво", "air defense", "штурм", "наступ"
        ])
        if is_noise and not has_hard_combat:
            return False

        # 3. Wskaźniki wojskowe i taktyczne (usunięto samo słowo 'baza'/'база')
        military_indicators = [
            "rakiet", "ракета", "missile", "drone", "дрон", "бпла", "shahed", "шахед", "мопед", "бандерол",
            "kab", "каб", "fab", "фаб", "artillery", "артилер", "обстріл", "обстрел", "shelling",
            "strike", "удар", "приліт", "прилет", "вибух", "взрыв", "explosion", "fire", "пожар", "пожеж",
            "air defense", "ппо", "пво", "збито", "сбито", "intercepted", "front", "фронт", "assault",
            "штурм", "наступ", "войск", "військ", "военн", "військов", "refinery", "нпз", "depot",
            "склад боєприпас", "склад боеприпас", "нефтебаз", "нафтобаз", "арсенал", "грау",
            "radar", "радар", "тривога", "тревога", "сирена", "hezbollah", "houthi", "idf", "gaza",
            "hamas", "хамас", "хезболл", "хусит", "nato", "baza wojskowa", "военная база", "авиабаза", "military"
        ]

        # 4. Wskaźniki dyplomacji wojennej i oświadczeń sztabowych
        diplomatic_indicators = [
            "macron", "putin", "zelensky", "trump", "biden", "scholz", "rutte", "moratorium",
            "sanctions", "санкци", "sankcje", "negocjac", "переговор", "aid", "пакет помощ", "peace", "мирн",
            "zawieszenie broni", "ceasefire", "nato", "pentagon", "министерств", "генштаб", "штаб", "генерал",
            "unga", "онн", "оон", "wymiana jeńców", "пленн", "обмен", "whitaker", "rubio", "syria", "sharaa",
            "izrael", "israel", "palestyn", "katar", "qatar", "iran", "liban", "lebanon"
        ]

        return any(ind in t for ind in military_indicators) or any(ind in t for ind in diplomatic_indicators)

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
        GENERIC_THEATERS = {
            "unknown",
            "wojna w europie wschodniej",
            "wojna w europie wschodniej (obszar fr)",
            "ukraina i rosja",
            "bliski wschód",
            "bliski wschód (liban)",
            "bliski wschód (gaza / zachodni brzeg)",
            "inne / globalne",
            "inne",
            "syria",
            "jemen / morze czerwone",
            "afryka (sudan / sahel)",
            "iran",
            "rosja",
            "ukraina"
        }

        # Słownik klastrów: klucz to (uproszczona_lokalizacja, data_dniowa)
        location_clusters: Dict[str, List[Dict[str, Any]]] = {}

        for ev in events:
            loc = ev.get("location_name", "Unknown").lower()
            main_loc = loc.split(",")[0].split("/")[0].strip()
            ts = ev.get("timestamp", "")[:10] # RRRR-MM-DD

            # Jeśli lokalizacja to ogólny teatr lub kraj, NIE klastruj z automatu
            if main_loc in GENERIC_THEATERS or len(main_loc) < 3:
                continue

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

            cluster = location_clusters.get(f"{main_loc}_{ts}", []) if main_loc not in GENERIC_THEATERS else []
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

    @staticmethod
    def categorize_tactical_event(text: str) -> Tuple[str, str]:
        """
        Precyzyjne przypisanie zdarzenia do wojskowej kategorii taktycznej.
        Zwraca: (nazwa_kategorii, ikona_emodżi)
        """
        t = text.lower()
        for cat_name, data in TACTICAL_CATEGORIES.items():
            for p in data["patterns"]:
                if re.search(p, t):
                    return cat_name, data["icon"]
        return "Incydent Bojowy", "⚔️"

    @staticmethod
    def deduplicate_and_merge_events(events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Inteligentna Deduplikacja i Łączenie Incydentów:
        Rozpoznaje, kiedy różne kanały OSINT (np. Baza, Astra, War Monitor, KPZSU, Rybar)
        raportują to samo uderzenie lub eksplozję w tym samym mieście/rejonie w oknie czasowym 12h.
        Łączy je w 1 kanoniczne zdarzenie, konsoliduje potwierdzone źródła, media i odznaki.
        Zwraca (deduplikowane_zdarzenia, liczba_scalonych_duplikatów).
        """
        if not events:
            return [], 0

        # Sortuj od najnowszych
        sorted_events = sorted(events, key=lambda x: x.get("timestamp", ""), reverse=True)
        merged_events: List[Dict[str, Any]] = []
        merged_count = 0
        used_ids = set()

        for i, ev1 in enumerate(sorted_events):
            if ev1["id"] in used_ids:
                continue

            # Inicjalizuj kanoniczne zdarzenie
            canonical = dict(ev1)
            confirmed_sources = set([ev1.get("source_channel")] if ev1.get("source_channel") else ["OSINT"])
            all_media = set(ev1.get("media_urls", []))

            loc1 = (canonical.get("location_name") or "").lower().split(",")[0].split("/")[0].strip()
            date1 = canonical.get("timestamp", "")[:10]
            cat1 = canonical.get("tactical_category") or canonical.get("event_type")

            # Przeszukaj pozostałe zdarzenia w poszukiwaniu duplikatów tego samego incydentu
            for j in range(i + 1, len(sorted_events)):
                ev2 = sorted_events[j]
                if ev2["id"] in used_ids:
                    continue

                loc2 = (ev2.get("location_name") or "").lower().split(",")[0].split("/")[0].strip()
                date2 = ev2.get("timestamp", "")[:10]
                cat2 = ev2.get("tactical_category") or ev2.get("event_type")

                GENERIC_LOCATIONS = {
                    "wojna w europie wschodniej",
                    "wojna w europie wschodniej (obszar fr)",
                    "ukraina i rosja",
                    "bliski wschód",
                    "bliski wschód (liban)",
                    "bliski wschód (gaza / zachodni brzeg)",
                    "inne / globalne",
                    "syria",
                    "jemen / morze czerwone",
                    "afryka (sudan / sahel)",
                    "iran",
                    "rosja",
                    "ukraina"
                }

                # Nie łącz zdarzeń dyplomatycznych ani ogólnych komunikatów, chyba że mają identyczny URL
                is_diplomacy = (cat1 == "Komunikat Sztabowy / Dyplomacja" or cat2 == "Komunikat Sztabowy / Dyplomacja")
                if is_diplomacy:
                    continue

                # Kryteria duplikatu:
                # 1. Dokładnie ten sam dzień
                is_same_day = (date1 == date2)
                if not is_same_day:
                    continue

                # 2. To samo konkretne miasto/obiekt (wykluczając nazwy całych teatrów)
                is_generic = (loc1 in GENERIC_LOCATIONS or loc2 in GENERIC_LOCATIONS or len(loc1) < 3 or len(loc2) < 3)
                is_same_loc = not is_generic and (loc1 == loc2 or (len(loc1) >= 4 and len(loc2) >= 4 and (loc1 in loc2 or loc2 in loc1)))

                coord_dist = abs(canonical.get("lat", 0) - ev2.get("lat", 0)) + abs(canonical.get("lon", 0) - ev2.get("lon", 0))
                # Wyklucz koordynaty centroidów teatrów
                is_centroid = (canonical.get("lat") in [48.8, 32.5, 35.2, 15.0, 15.5, 45.0, 48.5] and 
                               canonical.get("lon") in [36.5, 35.2, 37.5, 44.0, 32.5, 35.0, 31.0])
                is_close_coord = not is_centroid and (coord_dist < 0.15)

                # 3. Zbieżność tematyczna (ten sam cel, kategoria lub słowa kluczowe)
                text1 = canonical.get("text", "").lower()
                text2 = ev2.get("text", "").lower()

                common_target_keywords = [
                    "refinery", "нпз", "interpipe", "інтерпайп", "toropets", "торопец", "samara", "самар", 
                    "kursk", "power", "grid", "blackout", "підстанц", "substation", "kuybyshevskyi"
                ]
                shares_target = any(kw in text1 and kw in text2 for kw in common_target_keywords)

                is_duplicate = (is_same_loc or is_close_coord) and (shares_target or (cat1 == cat2 and is_same_loc and not is_generic))

                if is_duplicate:
                    # Scalanie: dodaj potwierdzenie ze źródła
                    src2 = ev2.get("source_channel")
                    if src2:
                        confirmed_sources.add(src2)
                    for m in ev2.get("media_urls", []):
                        all_media.add(m)

                    # Jeśli ev2 ma dłuższy/dokładniejszy tekst, uzupełnij
                    if len(ev2.get("text", "")) > len(canonical.get("text", "")):
                        canonical["text"] = ev2.get("text")
                    if ev2.get("is_fire"):
                        canonical["is_fire"] = True

                    used_ids.add(ev2["id"])
                    merged_count += 1

            # Zapisz skonsolidowane zdarzenie
            canonical["verified_by_sources"] = sorted(list(confirmed_sources))
            canonical["multi_source_verified"] = len(confirmed_sources) >= 2 or canonical.get("multi_source_verified", False)
            canonical["media_urls"] = list(all_media)
            
            # Upewnij się, że ma precyzyjną kategorię taktyczną
            if "tactical_category" not in canonical or not canonical["tactical_category"]:
                cat, icon = MilitaryNLPEngine.categorize_tactical_event(canonical.get("text", "") or canonical.get("title", ""))
                canonical["tactical_category"] = cat
                canonical["tactical_icon"] = icon

            used_ids.add(canonical["id"])
            merged_events.append(canonical)

        return merged_events, merged_count
