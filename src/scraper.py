import re
import html
import random
import hashlib
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
}

# Domyślne współrzędne centrów teatrów działań
THEATER_CENTROIDS = {
    "Ukraina i Rosja": (48.8, 36.5),
    "Bliski Wschód (Izrael / Liban / Gaza)": (32.5, 35.2),
    "Syria": (35.2, 37.5),
    "Jemen / Morze Czerwone": (15.0, 44.0),
    "Afryka (Sudan / Sahel)": (15.5, 32.5),
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
            "shot_shot", "DeepStateUA", "rybar", "clashreport"
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

        # 7. Rosja (rejony przygraniczne i uderzenia w głąb FR)
        if any(w in text_lower for w in [
            "samara", "kuybyshevskyi", "kursk", "belgorod", "bryansk", "rostov", "voronezh", 
            "lipetsk", "yaroslavl", "in russia", "russian territory", "tula", "kaluga", "ryazan",
            "novorossiysk", "tuapse", "krasnodar", "engels", "toropets", "tver", "россия", "рф", "курск", "белгород"
        ]):
            return "Rosja", "🇷🇺", "Wojna w Europie Wschodniej (Obszar FR)"

        # 8. Ukraina (słowa kluczowe)
        if "ukraine.liveuamap" in links_str or any(w in text_lower for w in [
            "ukraine", "kyiv", "kharkiv", "pokrovsk", "donetsk", "luhansk", "sbu", 
            "crimea", "zaporizhzhia", "kherson", "dnipro", "odesa", "sumy", "poltava",
            "cherkasy", "zhytomyr", "vinnytsia", "mykolaiv", "black sea", "shahed", 
            "zelensky", "defense forces", "interpipe", "україна", "украина", "зсу", "повітряні сили",
            "міг-31к", "київ", "ракетна небезпека", "тривога"
        ]):
            return "Ukraina", "🇺🇦", "Wojna w Europie Wschodniej"

        # 9. Kontekst specyficzny dla monitorowanego kanału
        if channel in ["kpszsu", "war_monitor", "vanek_nikolaev", "DeepStateUA", "uamap"]:
            return "Ukraina", "🇺🇦", "Wojna w Europie Wschodniej"
        if channel in ["astrapress", "bazabazon", "shot_shot"]:
            return "Rosja", "🇷🇺", "Wojna w Europie Wschodniej (Obszar FR)"
        if channel in ["rybar"]:
            return "Ukraina", "🇺🇦", "Wojna w Europie Wschodniej"

        # Domyślnie domena liveuamap.com często dotyczy Ukrainy
        if "liveuamap.com" in links_str and any(w in text_lower for w in ["missile", "drone", "air defense", "army", "forces"]):
            return "Ukraina", "🇺🇦", "Wojna w Europie Wschodniej"

        return "Inne / Globalne", "🌐", "Inne"

    def _determine_event_type(self, text: str) -> str:
        """Kategoryzuje typ incydentu wojskowego."""
        t = text.lower()
        if any(w in t for w in ["missile", "drone", "shahed", "ballistic", "cruise missile", "air strike", "airstrike", "bomb", "fab-", "glide bomb", "бандерол", "мопед", "реактив"]):
            return "Uderzenie Rakietowe / Dron"
        if any(w in t for w in ["artillery", "shelling", "mortar", "mlrs", "grad", "howitzer", "fired at", "обстріл", "обстрел"]):
            return "Ostrzał Artyleryjski"
        if any(w in t for w in ["clash", "assault", "offensive", "storming", "infantry", "troops", "trenches", "recaptured", "occupied", "repelled", "штурм", "наступ"]):
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
            "liveuamap"        # Globalny strumień Liveuamap
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

                        # Kanoniczny link do źródła taktycznego (bezpośredni post na Telegramie)
                        if data_post:
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
                            tactical_sources.append({
                                "name": MilitaryNLPEngine.format_source_name(channel or "OSINT", primary_link),
                                "url": primary_link
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
                        for photo in block.find_all("a", class_="tgme_widget_message_photo_wrap"):
                            style = photo.get("style", "")
                            m = re.search(r"background-image:url\('([^']+)'\)", style)
                            if m:
                                media_urls.append(m.group(1))

                        # Unikalny deterministyczny identyfikator zdarzenia
                        event_hash = hashlib.sha256(f"{data_post}_{raw_text[:100]}".encode()).hexdigest()[:16]
                        if event_hash in seen_ids:
                            continue
                        seen_ids.add(event_hash)

                        # NLP & Geokodowanie wielojęzyczne (cyrylica + alfabet łaciński)
                        cyrillic_loc = MilitaryNLPEngine.resolve_cyrillic_location(raw_text)
                        if cyrillic_loc:
                            lat, lon, loc_name, country, flag = cyrillic_loc
                            theater = "Wojna w Europie Wschodniej (Obszar FR)" if country == "Rosja" else "Wojna w Europie Wschodniej"
                        else:
                            country, flag, theater = self._determine_country_and_theater(raw_text, links, channel)
                            lat, lon, loc_name = self._extract_coordinates(raw_text, theater, event_hash)

                        event_type = self._determine_event_type(raw_text)
                        title = raw_text[:120] + "..." if len(raw_text) > 120 else raw_text
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
                            "text": self._sanitize_string(raw_text),
                            "location_name": loc_name,
                            "lat": lat,
                            "lon": lon,
                            "url": primary_link,
                            "tactical_sources": tactical_sources,
                            "media_urls": media_urls,
                            "weapons": weapons,
                            "target_type": target_type,
                            "is_fire": is_fire,
                            "threat_score": threat_score,
                            "source_channel": channel
                        }
                        events.append(event)

                    if oldest_post_num and page < max_pages - 1:
                        current_url = f"{base_url}?before={oldest_post_num}"
                    else:
                        break

                except Exception as e:
                    print(f"[AEGIS RADAR] Błąd w kanale {channel}, strona {page}: {e}")
                    break

        print(f"[AEGIS RADAR] Łącznie pobrano {len(events)} unikalnych zdarzeń z monitorowanych radarów.")
        return events

# Alias dla wstecznej kompatybilności
LiveuamapScraper = AegisOSINTScraper
