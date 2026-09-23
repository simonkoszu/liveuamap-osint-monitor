from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from nlp_engine import MilitaryNLPEngine

COUNTRY_METADATA = {
    "Ukraina": {"flag": "🇺🇦", "theater": "Wojna w Europie Wschodniej", "priority": 1},
    "Rosja": {"flag": "🇷🇺", "theater": "Wojna w Europie Wschodniej (Obszar FR)", "priority": 2},
    "Liban": {"flag": "🇱🇧", "theater": "Bliski Wschód (Liban)", "priority": 3},
    "Izrael i Palestyna": {"flag": "🇵🇸 🇮🇱", "theater": "Bliski Wschód (Gaza / Zachodni Brzeg)", "priority": 4},
    "Syria": {"flag": "🇸🇾", "theater": "Syria", "priority": 5},
    "Jemen": {"flag": "🇾🇪", "theater": "Jemen i Morze Czerwone", "priority": 6},
    "Iran": {"flag": "🇮🇷", "theater": "Bliski Wschód (Zatoka Perska)", "priority": 7},
    "Sudan": {"flag": "🇸🇩", "theater": "Afryka (Sudan)", "priority": 8},
    "Czujniki NASA": {"flag": "🛰️", "theater": "Orbita Satelitarna / NASA FIRMS", "priority": 9},
    "Inne / Globalne": {"flag": "🌐", "theater": "Inne", "priority": 10},
}

class ConflictAnalyzer:
    """
    Moduł analizy statystycznej z pełnym rozbiciem na poszczególne kraje:
    - Raport dzienny (24h), tygodniowy (7 dni), miesięczny (30 dni) dla każdego kraju osobno
    - Globalne podsumowanie i macierz porównawcza państw
    - Śledzenie zmian liczby zdarzeń od dnia dzisiejszego
    """
    def __init__(self, all_events: List[Dict[str, Any]], tracking_started_at: str = None):
        self.all_events = all_events
        self.now = datetime.now(timezone.utc)
        self.tracking_started_at = tracking_started_at or self.now.isoformat()

        from zoneinfo import ZoneInfo
        warsaw_tz = ZoneInfo("Europe/Warsaw")

        # Normalizacja pól zdarzeń (w tym NASA FIRMS i znaczniki czasu)
        for e in self.all_events:
            eid = str(e.get("id", ""))
            src = str(e.get("source", ""))
            ch = str(e.get("source_channel", ""))
            cat = str(e.get("tactical_category", ""))
            title = str(e.get("title", ""))

            is_nasa = (
                eid.startswith("nasa_firms") or
                "NASA FIRMS" in src or
                "NASA" in ch or
                "NASA" in cat or
                "NASA Satellites" in title or
                "Satelita NASA" in title
            )

            if is_nasa:
                e["is_nasa"] = True
                e["country"] = "Czujniki NASA"
                e["flag"] = "🛰️"
                e["source_channel"] = "NASA FIRMS"
                e["tactical_category"] = "Czujnik NASA FIRMS"
                e["tactical_icon"] = "🛰️"
                e["is_fire"] = True
                if not e.get("lon") and e.get("lng"):
                    e["lon"] = e.get("lng")

            if not e.get("timestamp"):
                raw_date = e.get("date") or e.get("added_at") or self.now.isoformat()
                if isinstance(raw_date, str) and " " in raw_date and "T" not in raw_date:
                    raw_date = raw_date.replace(" ", "T") + "+00:00"
                e["timestamp"] = raw_date

            # Konwersja czasu do strefy polskiej (Warszawa: CEST = UTC+2 latem, CET = UTC+1 zimą)
            ts = e.get("timestamp")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    dt_pl = dt.astimezone(warsaw_tz)
                    e["time_pl"] = dt_pl.strftime("%Y-%m-%d %H:%M")
                    e["time_pl_short"] = dt_pl.strftime("%H:%M")
                except Exception:
                    e["time_pl"] = ts[:16].replace("T", " ")
                    e["time_pl_short"] = ts[11:16]
            else:
                e["time_pl"] = ""
                e["time_pl_short"] = ""

    def _parse_iso(self, ts_str: str) -> Optional[datetime]:
        if not ts_str:
            return None
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            return None

    def _calculate_period_stats(self, events: List[Dict[str, Any]], prev_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        cnt = len(events)
        prev_cnt = len(prev_events)
        diff = cnt - prev_cnt
        pct = round(((cnt - prev_cnt) / prev_cnt * 100), 1) if prev_cnt > 0 else (100.0 if cnt > 0 else 0.0)

        types = Counter(e.get("event_type", "Inne") for e in events)
        locations = Counter(e.get("location_name", "Inne") for e in events)

        return {
            "count": cnt,
            "prev_count": prev_cnt,
            "diff": diff,
            "percent_change": pct,
            "types": dict(types.most_common(6)),
            "top_locations": dict(locations.most_common(5)),
            "key_events": events[:6]
        }

    def _determine_status(self, daily_cnt: int, weekly_cnt: int) -> tuple:
        if daily_cnt >= 5 or weekly_cnt >= 20:
            return "KRYTYCZNY", "bg-red-500/20 text-red-400 border-red-500/40"
        elif daily_cnt >= 2 or weekly_cnt >= 8:
            return "WYSOKI", "bg-amber-500/20 text-amber-400 border-amber-500/40"
        elif weekly_cnt > 0:
            return "UMIARKOWANY", "bg-blue-500/20 text-blue-400 border-blue-500/40"
        else:
            return "SPOKOJNY", "bg-slate-500/20 text-slate-400 border-slate-500/40"

    def analyze(self) -> Dict[str, Any]:
        t24h_ago = self.now - timedelta(days=1)
        t48h_ago = self.now - timedelta(days=2)
        t7d_ago = self.now - timedelta(days=7)
        t14d_ago = self.now - timedelta(days=14)
        t30d_ago = self.now - timedelta(days=30)
        t60d_ago = self.now - timedelta(days=60)
        today_midnight = self.now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Grupowanie zdarzeń według krajów
        country_events_map = defaultdict(list)
        events_by_date = defaultdict(int)

        for ev in self.all_events:
            c = ev.get("country")
            if not c or c not in COUNTRY_METADATA:
                # Jeśli starsze zdarzenie w bazie nie ma country, wywnioskuj z theater
                th = ev.get("theater", "")
                if "Ukraina" in th: c = "Ukraina"
                elif "Liban" in th: c = "Liban"
                elif "Bliski Wschód" in th or "Gaza" in th: c = "Izrael i Palestyna"
                elif "Syria" in th: c = "Syria"
                elif "Jemen" in th: c = "Jemen"
                elif "Sudan" in th: c = "Sudan"
                elif "Rosja" in th: c = "Rosja"
                else: c = "Inne / Globalne"
                ev["country"] = c
                ev["flag"] = COUNTRY_METADATA[c]["flag"]

            country_events_map[c].append(ev)

            dt = self._parse_iso(ev.get("timestamp"))
            if dt:
                events_by_date[dt.strftime("%Y-%m-%d")] += 1

        # Raporty per kraj
        countries_report = []
        for country_name, meta in sorted(COUNTRY_METADATA.items(), key=lambda x: x[1]["priority"]):
            ev_list = country_events_map.get(country_name, [])
            
            c_today = []
            c_24h = []
            c_prev_24h = []
            c_7d = []
            c_prev_7d = []
            c_30d = []
            c_prev_30d = []
            c_daily_timeline = defaultdict(int)

            for e in ev_list:
                dt = self._parse_iso(e.get("timestamp"))
                if not dt:
                    continue

                d_str = dt.strftime("%Y-%m-%d")
                c_daily_timeline[d_str] += 1

                if dt >= today_midnight:
                    c_today.append(e)
                if t24h_ago <= dt <= self.now:
                    c_24h.append(e)
                elif t48h_ago <= dt < t24h_ago:
                    c_prev_24h.append(e)

                if t7d_ago <= dt <= self.now:
                    c_7d.append(e)
                elif t14d_ago <= dt < t7d_ago:
                    c_prev_7d.append(e)

                if t30d_ago <= dt <= self.now:
                    c_30d.append(e)
                elif t60d_ago <= dt < t30d_ago:
                    c_prev_30d.append(e)

            daily_stats = self._calculate_period_stats(c_24h, c_prev_24h)
            weekly_stats = self._calculate_period_stats(c_7d, c_prev_7d)
            monthly_stats = self._calculate_period_stats(c_30d, c_prev_30d)

            status_label, status_class = self._determine_status(len(c_24h), len(c_7d))

            countries_report.append({
                "name": country_name,
                "flag": meta["flag"],
                "theater": meta["theater"],
                "total_events": len(ev_list),
                "events_today_count": len(c_today),
                "status_label": status_label,
                "status_class": status_class,
                "daily": daily_stats,
                "weekly": weekly_stats,
                "monthly": monthly_stats,
                "recent_events": sorted(ev_list, key=lambda e: e.get("timestamp", ""), reverse=True)
            })

        # Globalne agregacje
        all_today = [e for e in self.all_events if (self._parse_iso(e.get("timestamp")) or self.now) >= today_midnight]
        all_24h = [e for e in self.all_events if t24h_ago <= (self._parse_iso(e.get("timestamp")) or self.now) <= self.now]
        all_prev_24h = [e for e in self.all_events if t48h_ago <= (self._parse_iso(e.get("timestamp")) or self.now) < t24h_ago]
        all_7d = [e for e in self.all_events if t7d_ago <= (self._parse_iso(e.get("timestamp")) or self.now) <= self.now]
        all_prev_7d = [e for e in self.all_events if t14d_ago <= (self._parse_iso(e.get("timestamp")) or self.now) < t7d_ago]
        all_30d = [e for e in self.all_events if t30d_ago <= (self._parse_iso(e.get("timestamp")) or self.now) <= self.now]
        all_prev_30d = [e for e in self.all_events if t60d_ago <= (self._parse_iso(e.get("timestamp")) or self.now) < t30d_ago]

        # Timeline 30 dni
        timeline_days = sorted(events_by_date.keys())[-30:]
        timeline_counts = [events_by_date[d] for d in timeline_days]

        # Globalny Cross-Referencing i Weryfikacja Wieloźródłowa
        self.all_events = MilitaryNLPEngine.cross_verify_events(self.all_events)

        # Upewnij się, że każde zdarzenie ma taksonomię taktyczną
        for e in self.all_events:
            if "tactical_category" not in e or not e["tactical_category"]:
                cat, icon = MilitaryNLPEngine.categorize_tactical_event(e.get("text", "") or e.get("title", ""))
                e["tactical_category"] = cat
                e["tactical_icon"] = icon

        # Liczniki kategorii taktycznych
        tactical_counts = Counter(e.get("tactical_category", "Incydent Bojowy") for e in self.all_events)

        # Wzbogacenie punktów mapy o analizę militarną NLP
        map_points = []
        verified_count = sum(1 for e in self.all_events if e.get("multi_source_verified"))

        for e in self.all_events:
            lat = e.get("lat")
            lon = e.get("lon") or e.get("lng")
            if lat and lon:
                c = e.get("country", "Inne")
                text = e.get("text", "")
                weapons = MilitaryNLPEngine.extract_weapons(text)
                target = MilitaryNLPEngine.extract_target_type(text)
                has_fire = MilitaryNLPEngine.detect_fire_or_thermal(text) or e.get("is_fire", False)
                threat = MilitaryNLPEngine.calculate_threat_score(text, e.get("event_type", ""), c)

                map_points.append({
                    "id": e.get("id"),
                    "lat": lat,
                    "lon": lon,
                    "country": c,
                    "flag": e.get("flag", "🌐"),
                    "title": e.get("title_pl") or e.get("title"),
                    "text": e.get("text_pl") or text,
                    "title_pl": e.get("title_pl"),
                    "text_pl": e.get("text_pl"),
                    "type": e.get("event_type"),
                    "tactical_category": e.get("tactical_category", "Incydent Bojowy"),
                    "tactical_icon": e.get("tactical_icon", "⚔️"),
                    "location": e.get("location_name"),
                    "timestamp": e.get("timestamp"),
                    "time_pl": e.get("time_pl"),
                    "time_pl_short": e.get("time_pl_short"),
                    "url": e.get("url"),
                    "weapons": weapons,
                    "target_type": target,
                    "has_fire": has_fire,
                    "is_nasa": e.get("is_nasa", False),
                    "frp": e.get("frp", 0.0),
                    "threat_score": threat,
                    "source_channel": e.get("source_channel", "OSINT"),
                    "multi_source_verified": e.get("multi_source_verified", False),
                    "verified_by_sources": e.get("verified_by_sources", [e.get("source_channel", "OSINT")])
                })

        import hashlib
        import os
        from zoneinfo import ZoneInfo
        warsaw_tz = ZoneInfo("Europe/Warsaw")
        now_pl = self.now.astimezone(warsaw_tz)

        auth_salt = "aegis_tactical_salt_2026_osint"
        report_pin = os.getenv("REPORT_PIN", "7749").strip() or "7749"
        auth_hash = hashlib.sha256((auth_salt + report_pin).encode("utf-8")).hexdigest()
        carto_api_key = os.getenv("CARTO_API_KEY", "").strip() or "cb1_3u7r_1_3c8d42e4911c679a2d091c0d"

        all_events_sorted = sorted(self.all_events, key=lambda e: e.get("timestamp", ""), reverse=True)
        poland_threat = self._analyze_poland_threat(all_24h, all_7d)

        nasa_events = [e for e in all_events_sorted if e.get("is_nasa") or e.get("country") == "Czujniki NASA" or (e.get("id") or "").startswith("nasa_firms")]
        max_frp = 0.0
        for ne in nasa_events:
            try:
                max_frp = max(max_frp, float(ne.get("frp", 0.0) or 0.0))
            except (ValueError, TypeError):
                pass

        return {
            "generated_at": self.now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "generated_at_pl": now_pl.strftime("%Y-%m-%d %H:%M:%S CEST"),
            "today_date": self.now.strftime("%Y-%m-%d"),
            "today_date_pl": now_pl.strftime("%Y-%m-%d"),
            "total_events_in_db": len(self.all_events),
            "events_today_count": len(all_today),
            "multi_source_verified_count": verified_count,
            "tactical_categories": dict(tactical_counts.most_common()),
            "global_daily": self._calculate_period_stats(all_24h, all_prev_24h),
            "global_weekly": self._calculate_period_stats(all_7d, all_prev_7d),
            "global_monthly": self._calculate_period_stats(all_30d, all_prev_30d),
            "countries": countries_report,
            "all_events": all_events_sorted,
            "nasa_events": nasa_events,
            "nasa_events_count": len(nasa_events),
            "nasa_max_frp": round(max_frp, 1),
            "timeline": {
                "days": timeline_days,
                "counts": timeline_counts
            },
            "map_points": map_points,
            "poland_threat": poland_threat,
            "auth_salt": auth_salt,
            "auth_hash": auth_hash,
            "carto_api_key": carto_api_key
        }

    def _analyze_poland_threat(self, all_24h: List[Dict[str, Any]], all_7d: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Automatyczna Analiza Zegara Zagrożenia i Alerty Wczesnego Ostrzegania (Wojna Polska - Rosja / NATO).
        Oblicza wskaźniki ryzyka bezpośredniego konfliktu, incydentów przygranicznych,
        operacji hybrydowych oraz eskalacji strategicznej w cyklu godzinnym.
        """
        near_border_locs = [
            "lwów", "lviv", "wołyń", "volyn", "równe", "rivne", "stryj", "stryi", 
            "łuck", "lutsk", "jaworów", "yavoriv", "brześć", "grodno", "kaliningrad", 
            "królewiec", "suwałki", "bałtyk", "baltic", "morze bałtyckie", "zatoka gdańska"
        ]

        border_kinetic_24h = []
        border_kinetic_7d = []
        hybrid_24h = []
        nuclear_7d = []

        for e in all_7d:
            txt = ((e.get("title") or "") + " " + (e.get("title_pl") or "") + " " + 
                   (e.get("text") or "") + " " + (e.get("text_pl") or "")).lower()

            is_near_border = any(loc in txt for loc in near_border_locs) or (
                e.get("country") == "Ukraina" and any(w in txt for w in ["zachodniej ukrainy", "kurs na zachód", "western ukraine", "granicy z polską"])
            )
            is_kinetic = any(k in (e.get("tactical_category") or "") for k in ["Uderzenie", "Rakieta", "Dron", "Eksplozja"])

            if is_near_border and is_kinetic:
                border_kinetic_7d.append(e)
                if e in all_24h:
                    border_kinetic_24h.append(e)

            if any(w in txt for w in ["gps", "jamming", "zakłóc", "sabotaż", "sabotage", "dywersja", "cyber", "podpalen", "arson", "granic", "border", "baltyk", "bałtyk"]):
                if e in all_24h:
                    hybrid_24h.append(e)

            if any(w in txt for w in ["nuclear", "nuklear", "jądrow", "atom", "doktryn", "odstrasz", "strategic"]):
                nuclear_7d.append(e)

        # Składowe Prawdopodobieństwa (0-100%)
        # 1. Inwazja lądowa: stała niska baza (5-8%) - 90%+ sił lądowych FR uwiązane na Ukrainie i w Kursku
        ground_prob = 7

        # 2. Incydent kinetyczny (rakiety / drony przy granicy RP): wysokie ryzyko ze względu na naloty na zachodnią Ukrainę
        border_prob = min(80, 45 + len(border_kinetic_24h) * 8 + len(border_kinetic_7d) * 2)

        # 3. Wojna hybrydowa, sabotaż, GPS: stan ciągły krytyczny (80-92%)
        hybrid_prob = min(95, 78 + len(hybrid_24h) * 3)

        # 4. Zagrożenie nuklearne / eskalacja strategiczna: niskie (10-18%)
        nuclear_prob = min(25, 10 + len(nuclear_7d) * 2)

        # Łączny wskaźnik zagrożenia (Composite Threat Index: 0 - 100)
        composite_index = round(ground_prob * 0.15 + border_prob * 0.35 + hybrid_prob * 0.35 + nuclear_prob * 0.15)
        
        # Przeliczenie na minuty do północy (skala zegarowa: godzina 23:xx)
        # Indeks 70-75 mapuje się na 44-48 minut do północy (23:12 - 23:16)
        minutes_to_midnight = max(10, min(58, round(60 - (composite_index - 45) * 0.95)))
        clock_min = 60 - minutes_to_midnight
        threat_clock_time = f"23:{clock_min:02d}"

        # Status alertu
        if minutes_to_midnight <= 20:
            threat_level = "BARDZO WYSOKI (INCYDENTY KINETYCZNE PRZY GRANICY)"
            threat_color = "red"
            defcon = "DEFCON 2"
        elif minutes_to_midnight <= 50:
            threat_level = "PODWYŻSZONY (WOJNA HYBRYDOWA / PONIŻEJ PROGU ART. 5)"
            threat_color = "amber"
            defcon = "DEFCON 3"
        else:
            threat_level = "UMIARKOWANY (ODSTRASZANIE STRATEGICZNE)"
            threat_color = "blue"
            defcon = "DEFCON 4"

        # Generowanie alertów wczesnego ostrzegania
        alerts = []
        if border_kinetic_24h:
            alerts.append({
                "level": "CRITICAL",
                "badge": "🚨 KINETYCZNY PRZYGRANICZNY",
                "color_bg": "bg-red-950/70 border-red-700/60 text-red-200",
                "icon": "fa-triangle-exclamation text-red-400 animate-pulse",
                "title": f"Odnotowano {len(border_kinetic_24h)} uderzeń rakietowo-dronowych w korytarzu zachodniej Ukrainy w ciągu 24h",
                "desc": "Zwiększone ryzyko wtargnięcia zbłąkanych pocisków lub dronów w polską przestrzeń powietrzną. Wymagany stały dyżur bojowy par F-16 i posterunków radiolokacyjnych.",
                "timestamp": border_kinetic_24h[0].get("timestamp", self.now.strftime("%Y-%m-%d %H:%M UTC"))[:16].replace("T", " ")
            })
        else:
            alerts.append({
                "level": "WARNING",
                "badge": "⚠️ ALERT OPL / AIR POLICING",
                "color_bg": "bg-amber-950/60 border-amber-700/60 text-amber-200",
                "icon": "fa-jet-fighter text-amber-400",
                "title": "Podwyższona gotowość bojowa obrony powietrznej wschodniej granicy RP",
                "desc": "Rosyjskie lotnictwo strategiczne (Tu-95MS / MiG-31K) utrzymuje możliwość ataków na obwody graniczące z Polską (Wołyń, Lwów).",
                "timestamp": self.now.strftime("%Y-%m-%d %H:%M UTC")
            })

        if hybrid_24h:
            alerts.append({
                "level": "HIGH",
                "badge": "⚡ WOJNA HYBRYDOWA / EW",
                "color_bg": "bg-indigo-950/60 border-indigo-700/60 text-indigo-200",
                "icon": "fa-tower-broadcast text-indigo-400",
                "title": "Aktywność zakłócania sygnałów nawigacyjnych i dywersji w rejonie Bałtyku i granicy",
                "desc": "Zarejestrowano incydenty zakłócania systemów GPS/GNSS oraz presję dywersyjną służb specjalnych FR i RB w obszarze przygranicznym.",
                "timestamp": hybrid_24h[0].get("timestamp", self.now.strftime("%Y-%m-%d %H:%M UTC"))[:16].replace("T", " ")
            })

        if nuclear_7d:
            alerts.append({
                "level": "INFO",
                "badge": "🛡️ ODSTRASZANIE NATO",
                "color_bg": "bg-blue-950/60 border-blue-700/60 text-blue-200",
                "icon": "fa-shield-halved text-blue-400",
                "title": "Spójność parasola nuklearnego i konwencjonalnego NATO nad Polską",
                "desc": "Dowództwo Sojuszu i przedstawiciele USA potwierdzają bezwzględne obowiązywanie Art. 5 w razie naruszenia terytorium Rzeczypospolitej Polskiej.",
                "timestamp": nuclear_7d[0].get("timestamp", self.now.strftime("%Y-%m-%d %H:%M UTC"))[:16].replace("T", " ")
            })

        return {
            "threat_clock_time": threat_clock_time,
            "minutes_to_midnight": minutes_to_midnight,
            "threat_index": composite_index,
            "threat_level": threat_level,
            "defcon_equivalent": defcon,
            "threat_color": threat_color,
            "trend": "STABILNY Z ODCHYŁEM HYBRYDOWYM",
            "trend_icon": "fa-arrow-right",
            "vectors": {
                "ground_invasion": {
                    "name": "1. Bezpośrednia Inwazja Lądowa (Suwałki / Królewiec / Białoruś)",
                    "clock": "21:30",
                    "prob_pct": ground_prob,
                    "status": "BARDZO NISKIE",
                    "badge_color": "bg-emerald-950/70 text-emerald-300 border-emerald-700/50",
                    "bar_color": "bg-emerald-500",
                    "desc": "Ponad 90% wojsk lądowych FR uwiązanych na Ukrainie i w Kursku. Brak formowania zgrupowań uderzeniowych w Królewcu i na Białorusi."
                },
                "border_kinetic": {
                    "name": "2. Incydent Kinetyczny (Zbłąkana Rakieta / Dron przy granicy RP)",
                    "clock": "23:42",
                    "prob_pct": border_prob,
                    "status": "WYSOKIE",
                    "badge_color": "bg-amber-950/70 text-amber-300 border-amber-700/50",
                    "bar_color": "bg-amber-500",
                    "desc": "Zmasowane uderzenia nocne w zachodnią Ukrainę (Lwów, Stryj, Równe) wymuszają regularne poderwania par dyżurnych F-16."
                },
                "hybrid_sabotage": {
                    "name": "3. Wojna Hybrydowa, Sabotaż i Zakłócenia GPS",
                    "clock": "23:55",
                    "prob_pct": hybrid_prob,
                    "status": "KRYTYCZNE / TRWAJĄCE",
                    "badge_color": "bg-red-950/70 text-red-300 border-red-700/50",
                    "bar_color": "bg-red-500",
                    "desc": "Aktywne zakłócenia sygnałów nawigacyjnych nad Bałtykiem, cyberataki oraz operacje dywersyjne GRU w Europie Środkowej."
                },
                "nuclear_escalation": {
                    "name": "4. Eskalacja Nuklearna / BMR wobec Wschodniej Flanki",
                    "clock": "22:15",
                    "prob_pct": nuclear_prob,
                    "status": "NISKIE",
                    "badge_color": "bg-yellow-950/70 text-yellow-300 border-yellow-700/50",
                    "bar_color": "bg-yellow-500",
                    "desc": "Retoryka odstraszania politycznego na forum ONZ; doktryna nuklearna NATO i obecność sojusznicza gwarantują skuteczne odstraszanie."
                }
            },
            "alerts": alerts,
            "recommendations": [
                "Utrzymanie stałej gotowości bojowej naziemnych baterii OPL (Patriot / Wisła / Narew) na wschodniej granicy.",
                "Natychmiastowe procedury Air Policing (CAP F-16) podczas zmasowanych salw rakietowych na zachodnią Ukrainę.",
                "Podwyższona ochrona fizyczna i kontrwywiadowcza lotniska Rzeszów-Jasionka oraz szlaków kolejowych.",
                "Ciągły monitoring anomalii w paśmie GNSS/GPS nad Zatoką Gdańską i przesmykiem suwalskim."
            ]
        }
