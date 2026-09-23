import re
import html
import random
import hashlib
import email.utils
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from curl_cffi import requests
from nlp_engine import MilitaryNLPEngine

# Słownik współrzędnych geograficznych głównych miast i rejonów konfliktów (OSINT Geocoding)
GEOLOCATION_DB = {
    # Ukraina & Rosja (Front wschodni i północny)
    "pokrovsk": (48.2828, 37.1828, "Pokrowsk, Obwód doniecki"),
    "pokrovske": (48.2828, 37.1828, "Pokrowsk"),
    "samara": (53.1959, 50.1002, "Samara (Rafineria Kujbyszewska), Rosja"),
    "kuybyshevskyi": (53.1959, 50.1002, "Rafineria Kujbyszewska, Samara, Rosja"),
    "lipetsk": (52.6103, 39.5947, "Lipieck, Rosja"),
    "voronezh": (51.6608, 39.2003, "Woroneż, Rosja"),
    "yaroslavl": (57.6261, 39.8845, "Jarosław, Rosja"),
    "moscow": (55.7558, 37.6173, "Moskwa, Rosja"),
    "cherkasy": (49.4444, 32.0598, "Czerkasy, Ukraina"),
    "zhytomyr": (50.2547, 28.6587, "Żytomierz, Ukraina"),
    "vinnytsia": (49.2331, 28.4682, "Winnica, Ukraina"),
    "bushehr": (28.9234, 50.8203, "Buszehr / Zatoka, Iran"),
    "jam": (27.8183, 52.3278, "Jam, Buszehr, Iran"),
    "al-jawf": (16.5000, 45.0000, "Al-Dżauf, Jemen"),
    "jawf": (16.5000, 45.0000, "Al-Dżauf, Jemen"),
    "taiz": (13.5779, 44.0197, "Taiz, Jemen"),
    "chasiv yar": (48.5833, 37.8333, "Czasow Jar"),
    "toretsk": (48.3986, 37.8572, "Torećk"),
    "kurakhove": (47.9861, 37.2750, "Kurachowe"),
    "vuhledar": (47.7806, 37.2483, "Wuhłedar"),
    "kupiansk": (49.7078, 37.6169, "Kupiańsk"),
    "kharkiv": (49.9935, 36.2304, "Charków"),
    "kyiv": (50.4501, 30.5234, "Kijów"),
    "sumy": (50.9077, 34.7981, "Sumy"),
    "kursk": (51.7308, 36.1926, "Kursk, Rosja"),
    "sudzha": (51.1922, 35.2714, "Sudża, Obwód kurski"),
    "belgorod": (50.5954, 36.5873, "Biełgorod, Rosja"),
    "rostov": (47.2357, 39.7015, "Rostów nad Donem, Rosja"),
    "crimea": (45.3453, 34.4997, "Krym"),
    "sevastopol": (44.6167, 33.5254, "Sewastopol, Krym"),
    "odesa": (46.4825, 30.7233, "Odessa"),
    "odessa": (46.4825, 30.7233, "Odessa"),
    "mykolaiv": (46.9750, 31.9946, "Mikołajów"),
    "zaporizhzhia": (47.8388, 35.1396, "Zaporoże"),
    "kherson": (46.6354, 32.6169, "Chersoń"),
    "dnipro": (48.4647, 35.0462, "Dniepr"),
    "poltava": (49.5883, 34.5514, "Połtawa"),
    "lviv": (49.8397, 24.0297, "Lwów"),
    "donetsk": (48.0159, 37.8028, "Donieck"),
    "luhansk": (48.5740, 39.3078, "Ługańsk"),

    # Bliski Wschód (Izrael / Palestyna / Liban)
    "gaza": (31.5017, 34.4668, "Strefa Gazy"),
    "rafah": (31.2969, 34.2455, "Rafah, Gaza"),
    "khan younis": (31.3462, 34.3063, "Chan Junus, Gaza"),
    "jabalia": (31.5294, 34.4828, "Dżabalija, Gaza"),
    "west bank": (31.9522, 35.2332, "Zachodni Brzeg"),
    "jenin": (32.4608, 35.3006, "Dżanin, Zachodni Brzeg"),
    "tulkarm": (32.3117, 35.0286, "Tulkarm, Zachodni Brzeg"),
    "tel aviv": (32.0853, 34.7818, "Tel Awiw, Izrael"),
    "jerusalem": (31.7683, 35.2137, "Jerozolima"),
    "haifa": (32.7940, 34.9896, "Hajfa, Izrael"),
    "beirut": (33.8938, 35.5018, "Bejrut, Liban"),
    "dahieh": (33.8547, 35.5094, "Dahieh, Bejrut, Liban"),
    "southern lebanon": (33.2721, 35.3854, "Południowy Liban"),
    "tyre": (33.2704, 35.1969, "Tyr, Liban"),
    "sidon": (33.5631, 35.3689, "Sydon, Liban"),
    "nabatieh": (33.3772, 35.4839, "Nabatija, Liban"),
    "bekaa": (33.8463, 35.9020, "Dolina Bekaa, Liban"),

    # Syria
    "damascus": (33.5138, 36.2765, "Damaszek, Syria"),
    "aleppo": (36.2021, 37.1343, "Aleppo, Syria"),
    "idlib": (35.9306, 36.6339, "Idlib, Syria"),
    "homs": (34.7324, 36.7137, "Homs, Syria"),
    "deir ez-zor": (35.3359, 40.1408, "Dajr az-Zaur, Syria"),

    # Jemen i Morze Czerwone
    "sanaa": (15.3694, 44.1910, "Sana, Jemen"),
    "hodeidah": (14.7978, 42.9545, "Al-Hudajda, Jemen"),
    "aden": (12.7855, 45.0187, "Aden, Jemen"),
    "red sea": (18.0000, 39.5000, "Morze Czerwone"),
    "gulf of aden": (12.0000, 48.0000, "Zatoka Adeńska"),

    # Afryka (Sudan)
    "khartoum": (15.5007, 32.5599, "Chartum, Sudan"),
    "omdurman": (15.6500, 32.4833, "Omdurman, Sudan"),
    "el fasher": (13.6279, 25.3494, "Al-Faszir, Darfur, Sudan"),
    "port sudan": (19.6175, 37.2164, "Port Sudan, Sudan"),

    # Azja Południowa & Inne
    "waziristan": (32.3000, 69.8500, "Waziristan, Pakistan"),
    "kurram": (33.8167, 70.1667, "Kurram, Pakistan"),
    "duta khel": (32.9333, 69.8333, "Duta Khel, Waziristan, Pakistan"),
    "pryluky": (50.5895, 32.3857, "Przyłuci, Obwód czernihowski, Ukraina"),

    # Polska & Wschodnia Flanka NATO
    "braniewo": (54.3804, 19.8242, "Braniewo, Warmia, Polska"),
    "braniewa": (54.3804, 19.8242, "Braniewo, Warmia, Polska"),
    "braniewie": (54.3804, 19.8242, "Braniewo, Warmia, Polska"),
    "malbork": (54.0359, 19.0266, "Malbork (Baza Lotnicza), Polska"),
    "malborka": (54.0359, 19.0266, "Malbork (Baza Lotnicza), Polska"),
    "malborku": (54.0359, 19.0266, "Malbork (Baza Lotnicza), Polska"),
    "przewodów": (50.4706, 23.9317, "Przewodów, Lubelszczyzna, Polska"),
    "przewodowa": (50.4706, 23.9317, "Przewodów, Lubelszczyzna, Polska"),
    "przewodowie": (50.4706, 23.9317, "Przewodów, Lubelszczyzna, Polska"),
    "przewodow": (50.4706, 23.9317, "Przewodów, Lubelszczyzna, Polska"),
    "suwałki": (54.1115, 22.9309, "Przesmyk Suwalski, Polska"),
    "suwałk": (54.1115, 22.9309, "Przesmyk Suwalski, Polska"),
    "suwałkach": (54.1115, 22.9309, "Przesmyk Suwalski, Polska"),
    "suwalki": (54.1115, 22.9309, "Przesmyk Suwalski, Polska"),
    "suwalk": (54.1115, 22.9309, "Przesmyk Suwalski, Polska"),
    "suwalszczyzn": (54.1115, 22.9309, "Przesmyk Suwalski, Polska"),
    "warszawa": (52.2297, 21.0122, "Warszawa, Polska"),
    "warszawy": (52.2297, 21.0122, "Warszawa, Polska"),
    "warszawie": (52.2297, 21.0122, "Warszawa, Polska"),
    "rzeszów": (50.0412, 21.9991, "Rzeszów-Jasionka (Hub NATO), Polska"),
    "rzeszowa": (50.0412, 21.9991, "Rzeszów-Jasionka (Hub NATO), Polska"),
    "rzeszowie": (50.0412, 21.9991, "Rzeszów-Jasionka (Hub NATO), Polska"),
    "rzeszow": (50.0412, 21.9991, "Rzeszów-Jasionka (Hub NATO), Polska"),
    "jasionka": (50.1100, 22.0194, "Jasionka (Hub NATO), Polska"),
    "jasionki": (50.1100, 22.0194, "Jasionka (Hub NATO), Polska"),
    "jasionce": (50.1100, 22.0194, "Jasionka (Hub NATO), Polska"),
    "dorohusk": (51.1569, 23.8078, "Dorohusk (Granica), Polska"),
    "dorohuska": (51.1569, 23.8078, "Dorohusk (Granica), Polska"),
    "dorohusku": (51.1569, 23.8078, "Dorohusk (Granica), Polska"),
    "hrebenne": (50.2869, 23.5856, "Hrebenne (Granica), Polska"),
    "hrebennem": (50.2869, 23.5856, "Hrebenne (Granica), Polska"),
    "hrebennego": (50.2869, 23.5856, "Hrebenne (Granica), Polska"),
    "mierzeja wiślana": (54.3500, 19.3167, "Mierzeja Wiślana, Polska"),
    "mierzei wiślanej": (54.3500, 19.3167, "Mierzeja Wiślana, Polska"),
    "mierzeja wislana": (54.3500, 19.3167, "Mierzeja Wiślana, Polska"),
    "mierzei wislanej": (54.3500, 19.3167, "Mierzeja Wiślana, Polska"),
    "bałtyk": (54.8000, 18.5000, "Morze Bałtyckie"),
    "bałtyku": (54.8000, 18.5000, "Morze Bałtyckie"),
    "baltyk": (54.8000, 18.5000, "Morze Bałtyckie"),
    "baltyku": (54.8000, 18.5000, "Morze Bałtyckie"),
    "królewiec": (54.7104, 20.4522, "Obwód Królewiecki"),
    "królewca": (54.7104, 20.4522, "Obwód Królewiecki"),
    "królewcu": (54.7104, 20.4522, "Obwód Królewiecki"),
    "krolewiec": (54.7104, 20.4522, "Obwód Królewiecki"),
    "krolewca": (54.7104, 20.4522, "Obwód Królewiecki"),
    "kaliningrad": (54.7104, 20.4522, "Obwód Królewiecki"),
    "kaliningradu": (54.7104, 20.4522, "Obwód Królewiecki"),
}

# Domyślne współrzędne centrów teatrów działań
THEATER_CENTROIDS = {
    "Wschodnia Flanka NATO (Polska)": (52.2, 21.0),
    "Ukraina i Rosja": (48.8, 36.5),
    "Bliski Wschód (Izrael / Liban / Gaza)": (32.5, 35.2),
    "Syria": (35.2, 37.5),
    "Jemen / Morze Czerwone": (15.0, 44.0),
    "Afryka (Sudan / Sahel)": (15.5, 32.5),
    "Azja Południowa": (33.0, 70.0),
    "Inne / Globalne": (45.0, 35.0),
}

class AegisOSINTScraper:
    """
    Autonomiczny wojskowy silnik wywiadowczy Aegis OSINT Radar.
    Pobiera i parsuje dane taktyczne z bezpośrednich pierwotnych kanałów wywiadowczych (Zero Pośredników).
    """
    def __init__(self):
        self.telegram_channels = [
            "kpszsu", "war_monitor", "vanek_nikolaev", "astrapress", "bazabazon",
            "shot_shot", "DeepStateUA", "rybar", "clashreport", "r_combatfootage"
        ]

    def _sanitize_string(self, text: str, max_len: int = 2000) -> str:
        """Sanityzacja wejścia: zapobiega atakom XSS i wstrzykiwaniu niebezpiecznych znaków."""
        if not text:
            return ""
        clean = html.escape(text.strip())
        # Usuń znaki kontrolne poza standardowymi białymi znakami
        clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', clean)
        return clean[:max_len]

    def _determine_country_and_theater(self, text: str, links: List[str], channel: str = "") -> tuple:
        """
        Precyzyjne przyporządkowanie zdarzenia do konkretnego kraju i teatru działań,
        z uwzględnieniem kontekstu kanału źródłowego.
        Zwraca: (country_name, flag, theater)
        """
        text_lower = text.lower()
        links_str = " ".join(links).lower()

        # 0. Polska / Wschodnia Flanka NATO (Naruszenia przestrzeni, incydenty graniczne)
        if any(w in text_lower for w in [
            "braniewo", "malbork", "przewodów", "przewodow", "suwałki", "suwalki", "mierzeja wiślana",
            "dorohusk", "hrebenne", "jasionka", "rzeszów", "do rsz", "dorsz", "dowództwo operacyjne",
            "polska", "polski", "polską", "polskie", "polskiej", "polsce", "poland", "polish", "польш",
            "straż graniczna", "sztab generalny wp"
        ]):
            if any(w in text_lower for w in [
                "braniewo", "malbork", "przewod", "suwał", "suwal", "jasionk", "rzeszów", "rzeszow", "do rsz", "dorsz",
                "przestrzen", "granic", "wtargn", "narusz", "poderwan", "w polsce", "do polski", "nad polską",
                "nad polska", "w pobliżu polski", "przy granicy z polską", "polskie siły", "wojsko polskie", "defence24",
                "вторгся", "нарушил", "бранево"
            ]):
                return "Polska", "🇵🇱", "Wschodnia Flanka NATO (Polska)"

        # 1. Liban
        if "lebanon.liveuamap" in links_str or any(w in text_lower for w in ["lebanon", "lebanese", "beirut", "dahieh", "hezbollah", "southern lebanon", "nabatieh", "bekaa", "tyre", "sidon"]):
            return "Liban", "🇱🇧", "Bliski Wschód (Liban)"

        # 2. Izrael i Palestyna (Gaza / Zachodni Brzeg)
        if "israelpalestine.liveuamap" in links_str or any(w in text_lower for w in ["gaza", "rafah", "khan younis", "jabalia", "west bank", "jenin", "tulkarm", "hamas", "tel aviv", "jerusalem", "idf", "gaza strip"]):
            return "Izrael i Palestyna", "🇵🇸 🇮🇱", "Bliski Wschód (Gaza / Zachodni Brzeg)"

        # 3. Syria
        if "syria.liveuamap" in links_str or any(w in text_lower for w in ["syria", "damascus", "aleppo", "idlib", "homs", "deir ez-zor", "assad", "latakia"]):
            return "Syria", "🇸🇾", "Syria"

        # 4. Jemen i Morze Czerwone
        if "yemen.liveuamap" in links_str or any(w in text_lower for w in ["yemen", "houthi", "sanaa", "hodeidah", "red sea", "gulf of aden", "bab el-mandeb", "us central command", "centcom"]):
            return "Jemen", "🇾🇪", "Jemen i Morze Czerwone"

        # 5. Sudan
        if "sudan.liveuamap" in links_str or any(w in text_lower for w in ["sudan", "khartoum", "rsf", "saf", "darfur", "el fasher", "omdurman"]):
            return "Sudan", "🇸🇩", "Afryka (Sudan)"

        # 6. Iran i Zatoka Perska
        if "iran.liveuamap" in links_str or any(w in text_lower for w in [
            "iran", "iranian", "tehran", "bushehr", "jam", "shiraz", "hormuz", 
            "strait of hormuz", "persian gulf", "qeshm", "khandab", "natanz", "isfahan", "kuwait"
        ]):
            return "Iran", "🇮🇷", "Bliski Wschód (Zatoka Perska)"

        # 7. Pakistan i Afganistan
        if any(w in text_lower for w in ["pakistan", "pakistani", "taliban", "afghanistan", "waziristan", "kurram"]):
            return "Pakistan / Afganistan", "🇵🇰 🇦🇫", "Azja Południowa"

        # 8. Rosja (rejony przygraniczne i uderzenia w głąb FR)
        if any(w in text_lower for w in [
            "samara", "kuybyshevskyi", "kursk", "belgorod", "bryansk", "rostov", "voronezh", 
            "lipetsk", "yaroslavl", "in russia", "russian territory", "tula", "kaluga", "ryazan",
            "novorossiysk", "tuapse", "krasnodar", "engels", "toropets", "tver", "россия", "рф", "курск", "белгород"
        ]):
            return "Rosja", "🇷🇺", "Wojna w Europie Wschodniej (Obszar FR)"

        # 9. Ukraina (słowa kluczowe)
        if "ukraine.liveuamap" in links_str or any(w in text_lower for w in [
            "ukraine", "kyiv", "kharkiv", "pokrovsk", "donetsk", "luhansk", "sbu", 
            "crimea", "zaporizhzhia", "kherson", "dnipro", "odesa", "sumy", "poltava",
            "cherkasy", "zhytomyr", "vinnytsia", "mykolaiv", "black sea", "shahed", 
            "zelensky", "defense forces", "interpipe", "україна", "украина", "зсу", "повітряні сили",
            "міг-31к", "київ", "ракетна небезпека", "тривога"
        ]):
            return "Ukraina", "🇺🇦", "Wojna w Europie Wschodniej"

        # 10. Kontekst specyficzny dla monitorowanego kanału
        if channel in ["kpszsu", "war_monitor", "vanek_nikolaev", "DeepStateUA", "uamap"]:
            return "Ukraina", "🇺🇦", "Wojna w Europie Wschodniej"
        if channel in ["astrapress", "bazabazon", "shot_shot"]:
            return "Rosja", "🇷🇺", "Wojna w Europie Wschodniej (Obszar FR)"
        if channel in ["rybar"]:
            return "Ukraina", "🇺🇦", "Wojna w Europie Wschodniej"
        if channel in ["defence24"]:
            return "Polska", "🇵🇱", "Wschodnia Flanka NATO (Polska)"

        # Domyślnie domena liveuamap.com często dotyczy Ukrainy
        if "liveuamap.com" in links_str and any(w in text_lower for w in ["missile", "drone", "air defense", "army", "forces"]):
            return "Ukraina", "🇺🇦", "Wojna w Europie Wschodniej"

        return "Inne / Globalne", "🌐", "Inne"

    def _determine_event_type(self, text: str) -> str:
        """Kategoryzuje typ incydentu wojskowego."""
        t = text.lower()
        if any(w in t for w in ["naruszeni", "przestrzeń powietrzn", "przestrzeni powietrzn", "airspace", "wtargn", "вторгся", "нарушил воздуш", "niezidentyfikowan"]):
            return "Incydent Powietrzny / Naruszenie Granicy"
        if any(w in t for w in ["missile", "drone", "shahed", "ballistic", "cruise missile", "air strike", "airstrike", "bomb", "fab-", "glide bomb", "uav", "fpv", "бандерол", "мопед", "реактив"]):
            return "Uderzenie Rakietowe / Dron"
        if any(w in t for w in ["artillery", "shelling", "mortar", "mlrs", "grad", "howitzer", "fired at", "обстріл", "обстрел"]):
            return "Ostrzał Artyleryjski"
        if any(w in t for w in ["clash", "assault", "offensive", "storming", "infantry", "troops", "soldiers", "combat", "taliban", "trenches", "recaptured", "occupied", "repelled", "firefight", "штурм", "наступ"]):
            return "Starcie Lądowe"
        if any(w in t for w in ["air defense", "intercepted", "shot down", "destroyed in air", "repelled attack", "ппо", "пво", "збито"]):
            return "Obrona Przeciwlotnicza"
        if any(w in t for w in ["refinery", "depot", "plant", "substation", "power line", "railway", "bridge", "pipeline", "oil", "нпз", "нафтобаз", "нефтебаз"]):
            return "Infrastruktura & Logistyka"
        if any(w in t for w in ["ship", "vessel", "naval", "boat", "sea drone", "frigate", "submarine", "магура"]):
            return "Działania Morskie"
        if any(w in t for w in ["statement", "agreement", "aid", "sanctions", "peace", "negotiations", "declared", "meeting"]):
            return "Komunikat / Dyplomacja"
        return "Incydent Bojowy"

    def _extract_coordinates(self, text: str, theater: str, event_id: str) -> tuple:
        """Znajduje współrzędne miejscowości lub przypisuje reprezentatywny punkt teatru."""
        t = text.lower()
        for place, (lat, lon, name) in GEOLOCATION_DB.items():
            # Wyszukiwanie jako całe słowo
            if re.search(r'\b' + re.escape(place) + r'\b', t):
                return lat, lon, name

        # Jeśli brak konkretnego miasta, bierzemy centroid teatru z mikro-rozproszeniem (jitter)
        base_lat, base_lon = THEATER_CENTROIDS.get(theater, (48.0, 35.0))
        # Deterministyczny jitter na bazie SHA256 ID zdarzenia (aby punkty nie leżały dokładnie w jednym punkcie)
        h = int(hashlib.sha256(event_id.encode()).hexdigest()[:6], 16)
        jitter_lat = ((h % 1000) / 1000.0 - 0.5) * 0.4
        jitter_lon = (((h >> 10) % 1000) / 1000.0 - 0.5) * 0.6

        return round(base_lat + jitter_lat, 4), round(base_lon + jitter_lon, 4), theater

    def fetch_latest_events(self, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        Pobiera i parsuje zdarzenia z publicznych kanałów Liveuamap oraz powiązanych strumieni,
        z opcjonalnym stronicowaniem wstecz (?before=) dla pobrania pełnej historii taktycznej.
        """
        events = []
        seen_ids = set()
        channels = [
            "kpszsu",          # Dowództwo Sił Powietrznych UA (oficjalne raporty i alarmy)
            "war_monitor",     # Radar wczesnego ostrzegania (wektory rakiet i Shahedów)
            "vanek_nikolaev",  # Wojskowy radar OPL (2.5M obserwujących)
            "astrapress",      # Niezależny OSINT w Rosji (uderzenia w rafinerie i bazy)
            "bazabazon",       # Baza - wideo i pożary w głębi FR
            "shot_shot",       # Shot - raporty z obwodów granicznych i uderzeń
            "DeepStateUA",     # Główna mapa zmian frontu w Ukrainie
            "rybar",           # Rosyjskie mapy operacyjne i weryfikacja krzyżowa
            "clashreport",     # Globalny radar starć bojowych (Bliski Wschód, Morze Czerwone, Sudan)
            "liveuamap",       # Globalny strumień Liveuamap
            "r_combatfootage"  # Reddit r/CombatFootage (autonomiczny strumień wideo i walk frontowych)
        ]

        for channel in channels:
            base_url = f"https://t.me/s/{channel}"
            current_url = base_url

            for page in range(max_pages):
                try:
                    r = requests.get(current_url, impersonate="chrome120", timeout=15)
                    if r.status_code != 200:
                        break

                    soup = BeautifulSoup(r.text, "html.parser")
                    msg_blocks = soup.find_all("div", class_="tgme_widget_message")
                    if not msg_blocks:
                        break

                    oldest_post_num = None
                    for block in reversed(msg_blocks):
                        data_post = block.get("data-post", "")
                        if "/" in data_post:
                            try:
                                p_num = int(data_post.split("/")[-1])
                                if oldest_post_num is None or p_num < oldest_post_num:
                                    oldest_post_num = p_num
                            except ValueError:
                                pass

                        text_div = block.find("div", class_="tgme_widget_message_text")
                        if not text_div:
                            continue

                        raw_text = text_div.get_text(separator=" ", strip=True)
                        if not raw_text or len(raw_text) < 15:
                            continue

                        # Filtr Antyszumowy (Noise Reduction Filter)
                        # Odrzuca opinie polityczne, zbiórki i nie-wojskowy czat
                        if not MilitaryNLPEngine.is_military_event(raw_text):
                            continue

                        # Wyciągnięcie prawdziwego znacznika czasu publikacji wiadomości
                        time_tag = block.find(lambda t: t.name == "time" and t.has_attr("datetime"))
                        if not time_tag:
                            date_a = block.find("a", class_="tgme_widget_message_date")
                            if date_a:
                                time_tag = date_a.find("time")

                        timestamp = time_tag.get("datetime") if time_tag and time_tag.get("datetime") else None
                        if not timestamp:
                            continue  # Pomiń wpisy bez weryfikowalnego znacznika czasu publikacji

                        # Linki w treści (wyciągamy tylko poprawne linki zewnętrzne, filtrując zapytania wewnętrzne typu ?q=...)
                        links = [
                            a.get("href") for a in text_div.find_all("a")
                            if a.get("href") and (a.get("href").startswith("http://") or a.get("href").startswith("https://"))
                        ]
                        reddit_links = [l for l in links if "redd.it" in l or "reddit.com" in l]

                        # Wykrywanie bezpośredniego wideo MP4 (np. z r/CombatFootage) i miniatury
                        video_tag = block.find("video")
                        video_url = video_tag.get("src") if video_tag and video_tag.get("src") else None

                        video_thumb = None
                        thumb_tag = block.find(class_=lambda c: c and "thumb" in c)
                        if thumb_tag and thumb_tag.get("style"):
                            m_thumb = re.search(r"background-image:url\('([^']+)'\)", thumb_tag.get("style"))
                            if m_thumb:
                                video_thumb = m_thumb.group(1)

                        # Kanoniczny link do źródła taktycznego
                        if channel == "r_combatfootage" and reddit_links:
                            primary_link = reddit_links[0]
                        elif data_post:
                            primary_link = f"https://t.me/{data_post}"
                        elif channel:
                            primary_link = f"https://t.me/{channel}"
                        elif links:
                            primary_link = links[0]
                        else:
                            primary_link = "https://liveuamap.com"

                        # Wszystkie wykryte linki źródłowe i cytowane w poście (Tactical Sources)
                        tactical_sources = []
                        if primary_link:
                            src_name = "Reddit (r/CombatFootage)" if ("redd.it" in primary_link or "reddit.com" in primary_link) else MilitaryNLPEngine.format_source_name(channel or "OSINT", primary_link)
                            tactical_sources.append({
                                "name": src_name,
                                "url": primary_link
                            })

                        # Dodaj bezpośredni odnośnik Telegram jeśli główny to Reddit
                        if channel == "r_combatfootage" and data_post:
                            tg_url = f"https://t.me/{data_post}"
                            if not any(x.get("url") == tg_url for x in tactical_sources):
                                tactical_sources.append({
                                    "name": "Telegram (#r_combatfootage)",
                                    "url": tg_url
                                })

                        for link in links:
                            if link and link != primary_link and not any(x.get("url") == link for x in tactical_sources):
                                if not any(ign in link for ign in ["?q=", "?start=", "t.me/s/", "t.me/share"]):
                                    src_name = MilitaryNLPEngine.format_source_name_from_url(link)
                                    tactical_sources.append({
                                        "name": src_name,
                                        "url": link
                                    })

                        # Zdjęcia / podglądy multimediów
                        media_urls = []
                        if video_thumb:
                            media_urls.append(video_thumb)
                        for photo in block.find_all("a", class_="tgme_widget_message_photo_wrap"):
                            style = photo.get("style", "")
                            m = re.search(r"background-image:url\('([^']+)'\)", style)
                            if m and m.group(1) not in media_urls:
                                media_urls.append(m.group(1))

                        # Unikalny deterministyczny identyfikator zdarzenia
                        event_hash = hashlib.sha256(f"{data_post}_{raw_text[:100]}".encode()).hexdigest()[:16]
                        if event_hash in seen_ids:
                            continue
                        seen_ids.add(event_hash)

                        # Oczyszczenie tekstu z URL i uchwytów kanału dla czystych tytułów
                        clean_text = raw_text
                        if channel == "r_combatfootage":
                            clean_text = re.sub(r'https?://(?:redd\.it|reddit\.com|t\.me|m\.youtube\.com|youtube\.com)/\S+', '', clean_text)
                            clean_text = re.sub(r'@r_combatfootage\b', '', clean_text).strip()
                            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                            if len(clean_text) < 15:
                                clean_text = raw_text

                        # NLP & Geokodowanie wielojęzyczne (cyrylica + alfabet łaciński)
                        cyrillic_loc = MilitaryNLPEngine.resolve_cyrillic_location(raw_text)
                        if cyrillic_loc:
                            lat, lon, loc_name, country, flag = cyrillic_loc
                            if country == "Rosja":
                                theater = "Wojna w Europie Wschodniej (Obszar FR)"
                            elif country == "Polska":
                                theater = "Wschodnia Flanka NATO (Polska)"
                            else:
                                theater = "Wojna w Europie Wschodniej"
                        else:
                            country, flag, theater = self._determine_country_and_theater(raw_text, links, channel)
                            lat, lon, loc_name = self._extract_coordinates(raw_text, theater, event_hash)

                        event_type = self._determine_event_type(raw_text)
                        title = clean_text[:120] + "..." if len(clean_text) > 120 else clean_text
                        title = re.sub(r'\s+', ' ', title).strip()

                        weapons = MilitaryNLPEngine.extract_weapons(raw_text)
                        target_type = MilitaryNLPEngine.extract_target_type(raw_text)
                        is_fire = MilitaryNLPEngine.detect_fire_or_thermal(raw_text)
                        threat_score = MilitaryNLPEngine.calculate_threat_score(raw_text, event_type, country)
                        tactical_category, tactical_icon = MilitaryNLPEngine.categorize_tactical_event(raw_text)

                        event = {
                            "id": event_hash,
                            "timestamp": timestamp,
                            "country": country,
                            "flag": flag,
                            "theater": theater,
                            "event_type": event_type,
                            "tactical_category": tactical_category,
                            "tactical_icon": tactical_icon,
                            "title": self._sanitize_string(title),
                            "text": self._sanitize_string(clean_text),
                            "location_name": loc_name,
                            "lat": lat,
                            "lon": lon,
                            "url": primary_link,
                            "tactical_sources": tactical_sources,
                            "media_urls": media_urls,
                            "video_url": video_url,
                            "is_video": bool(video_url),
                            "weapons": weapons,
                            "target_type": target_type,
                            "is_fire": is_fire,
                            "threat_score": threat_score,
                            "source_channel": "r_combatfootage" if channel == "r_combatfootage" else channel
                        }
                        events.append(event)

                    if oldest_post_num and page < max_pages - 1:
                        current_url = f"{base_url}?before={oldest_post_num}"
                    else:
                        break

                except Exception as e:
                    print(f"[AEGIS RADAR] Błąd w kanale {channel}, strona {page}: {e}")
                    break

        # 2. Pobieranie z polskiego radaru wojskowo-obronnego Defence24 (RSS)
        print("[AEGIS RADAR] Skanowanie polskiego feedu wojskowego Defence24 RSS...")
        try:
            d24_events = self._fetch_defence24_rss(max_items=35)
            d24_added = 0
            for dev in d24_events:
                if dev["id"] not in seen_ids:
                    seen_ids.add(dev["id"])
                    events.append(dev)
                    d24_added += 1
            print(f"[AEGIS RADAR] Zaimportowano {d24_added} meldunków operacyjnych z Defence24.")
        except Exception as e:
            print(f"[AEGIS RADAR] Błąd pobierania feedu Defence24: {e}")

        print(f"[AEGIS RADAR] Łącznie pobrano {len(events)} unikalnych zdarzeń z monitorowanych radarów.")
        return events

    def _fetch_defence24_rss(self, max_items: int = 35) -> List[Dict[str, Any]]:
        """
        Pobiera najświeższe depesze obronne i meldunki wojskowe z polskiego portalu Defence24 (RSS).
        Błyskawiczny czas reakcji dla incydentów w polskiej przestrzeni powietrznej, komunikatów DO RSZ i MON.
        """
        events = []
        rss_url = "https://defence24.pl/rss"
        try:
            r = requests.get(rss_url, impersonate="chrome120", timeout=15)
            if r.status_code != 200:
                print(f"[AEGIS RADAR] Defence24 RSS zwrócił kod {r.status_code}")
                return events

            root = ET.fromstring(r.content)
            channel = root.find("channel")
            if channel is None:
                return events

            items = channel.findall("item")
            for it in items[:max_items]:
                title = it.findtext("title", "").strip()
                desc = it.findtext("description", "").strip()
                link = it.findtext("link", "").strip()
                pub_date_str = it.findtext("pubDate", "").strip()
                guid = it.findtext("guid", "").strip() or link

                full_text = f"{title}. {desc}".strip()
                if not full_text or len(full_text) < 15:
                    continue

                # Filtr antyszumowy NLP dla wydarzeń militarnych
                if not MilitaryNLPEngine.is_military_event(full_text):
                    continue

                # Konwersja czasu do formatu ISO 8601 UTC
                timestamp = None
                if pub_date_str:
                    try:
                        dt = email.utils.parsedate_to_datetime(pub_date_str)
                        timestamp = dt.astimezone(timezone.utc).isoformat()
                    except Exception:
                        pass
                if not timestamp:
                    timestamp = datetime.now(timezone.utc).isoformat()

                # Zdjęcie / media (Yahoo MRSS)
                media_urls = []
                for child in it:
                    if child.tag.endswith("content") and "url" in child.attrib:
                        media_urls.append(child.attrib["url"])
                    elif child.tag.endswith("thumbnail") and "url" in child.attrib:
                        if not media_urls:
                            media_urls.append(child.attrib["url"])
                    elif child.tag == "enclosure" and "url" in child.attrib:
                        media_urls.append(child.attrib["url"])

                # Określenie kraju i teatru działań
                country, flag, theater = self._determine_country_and_theater(full_text, [link], "defence24")
                event_hash = hashlib.sha256(f"defence24_{guid}".encode()).hexdigest()[:16]

                # Geokodowanie
                lat, lon, loc_name = self._extract_coordinates(full_text, theater, event_hash)

                event_type = self._determine_event_type(full_text)
                tactical_category, tactical_icon = MilitaryNLPEngine.categorize_tactical_event(full_text)
                weapons = MilitaryNLPEngine.extract_weapons(full_text)
                target_type = MilitaryNLPEngine.extract_target_type(full_text)
                is_fire = MilitaryNLPEngine.detect_fire_or_thermal(full_text)
                threat_score = MilitaryNLPEngine.calculate_threat_score(full_text, event_type, country)

                clean_title = self._sanitize_string(title[:120] + "..." if len(title) > 120 else title)
                clean_text = self._sanitize_string(full_text)

                event = {
                    "id": event_hash,
                    "timestamp": timestamp,
                    "country": country,
                    "flag": flag,
                    "theater": theater,
                    "event_type": event_type,
                    "tactical_category": tactical_category,
                    "tactical_icon": tactical_icon,
                    "title": clean_title,
                    "text": clean_text,
                    "title_pl": clean_title,
                    "text_pl": clean_text,
                    "location_name": loc_name,
                    "lat": lat,
                    "lon": lon,
                    "url": link,
                    "tactical_sources": [
                        {
                            "name": "Defence24",
                            "url": link
                        }
                    ],
                    "media_urls": media_urls,
                    "video_url": None,
                    "is_video": False,
                    "weapons": weapons,
                    "target_type": target_type,
                    "is_fire": is_fire,
                    "threat_score": threat_score,
                    "source_channel": "defence24",
                    "verified_by_sources": ["defence24"],
                    "multi_source_verified": False
                }
                events.append(event)

        except Exception as e:
            print(f"[AEGIS RADAR] Błąd pobierania Defence24 RSS: {e}")

        return events

# Alias dla wstecznej kompatybilności
LiveuamapScraper = AegisOSINTScraper
