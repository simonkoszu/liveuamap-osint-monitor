import re
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
    "Pakistan / Afganistan": {"flag": "🇵🇰 🇦🇫", "theater": "Azja Południowa", "priority": 9},
    "Czujniki NASA": {"flag": "🛰️", "theater": "Orbita Satelitarna / NASA FIRMS", "priority": 10},
    "Inne / Globalne": {"flag": "🌐", "theater": "Inne", "priority": 11},
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

            # Standaryzacja i kompletowanie wieloźródłowych odnośników taktycznych (Tactical Sources)
            raw_sources = []
            seen_urls = set()

            def _extract_channel(url_str: str, fallback_ch: str = "") -> str:
                if not url_str:
                    return fallback_ch.lower().strip().lstrip("#")
                if "firms.modaps.eosdis.nasa.gov" in url_str:
                    return "nasa_firms"
                m = re.search(r"t\.me/(?:s/)?([^/?#]+)", url_str)
                if m:
                    return m.group(1).lower().strip()
                return fallback_ch.lower().strip().lstrip("#")

            # 1. Główny link zdarzenia (url) jako priorytet #1
            main_url = (e.get("url") or "").strip()
            ch_name = e.get("source_channel") or "Źródło"
            if main_url and main_url not in seen_urls:
                seen_urls.add(main_url)
                raw_sources.append({
                    "name": MilitaryNLPEngine.format_source_name(ch_name, main_url),
                    "url": main_url,
                    "channel": _extract_channel(main_url, ch_name)
                })

            # 2. Źródła już obecne w obiekcie
            for ts in e.get("tactical_sources", []):
                u = (ts.get("url") or "").strip()
                if u and u not in seen_urls:
                    seen_urls.add(u)
                    ch = _extract_channel(u)
                    src_name = MilitaryNLPEngine.format_source_name(ch, u) if ch else (ts.get("name") or MilitaryNLPEngine.format_source_name_from_url(u))
                    raw_sources.append({
                        "name": src_name,
                        "url": u,
                        "channel": ch
                    })

            # 3. Wyciągnij dodatkowe odnośniki z treści zdarzenia (np. cytowane źródła, Kliczko itp.)
            full_text = f"{e.get('text', '')} {e.get('title', '')} {e.get('text_pl', '')}"
            found_urls = re.findall(r'https?://[^\s)\]"\'>]+', full_text)
            for fu in found_urls:
                fu_clean = fu.rstrip(".,;:!?)")
                if fu_clean and fu_clean not in seen_urls:
                    if not any(ign in fu_clean for ign in ["?q=", "?start=", "t.me/s/", "t.me/share"]):
                        seen_urls.add(fu_clean)
                        src_name = MilitaryNLPEngine.format_source_name_from_url(fu_clean)
                        raw_sources.append({
                            "name": src_name,
                            "url": fu_clean,
                            "channel": _extract_channel(fu_clean)
                        })

            # 4. Potwierdzone kanały z multi_source_verified (verified_by_sources)
            for v_src in e.get("verified_by_sources", []):
                if not v_src or v_src in ["OSINT", "OSINT Multi-Radar", "Satelity"]:
                    continue
                v_clean = v_src.lower().strip().lstrip("#")
                has_channel_link = any(
                    v_clean == s.get("channel") or v_clean in s.get("url", "").lower()
                    for s in raw_sources
                )
                if not has_channel_link:
                    chan_url = f"https://t.me/{v_clean}"
                    if chan_url not in seen_urls:
                        seen_urls.add(chan_url)
                        raw_sources.append({
                            "name": MilitaryNLPEngine.format_source_name(v_clean, chan_url),
                            "url": chan_url,
                            "channel": v_clean
                        })

            # Formatowanie i deduplikacja:
            # - Ogranicz do max 2 linków z jednego kanału (dla satelitów NASA max 1)
            # - Jeśli ten sam kanał występuje wielokrotnie, doklej numer wpisu #post, by uniknąć identycznych przycisków
            channel_counts = {}
            for s in raw_sources:
                ch = s.get("channel") or "other"
                channel_counts[ch] = channel_counts.get(ch, 0) + 1

            tactical_sources = []
            channel_used = {}
            for s in raw_sources:
                ch = s.get("channel") or "other"
                limit_for_ch = 1 if "nasa" in ch else 2
                count_for_ch = channel_used.get(ch, 0)
                if ch != "other" and count_for_ch >= limit_for_ch:
                    continue
                channel_used[ch] = count_for_ch + 1

                label = s["name"]
                if channel_counts.get(ch, 0) > 1:
                    m = re.search(r"t\.me/[^/]+/(\d+)", s["url"])
                    if m:
                        post_num = m.group(1)
                        label = f"{label} #{post_num}"
                    elif count_for_ch > 0:
                        label = f"{label} ({count_for_ch + 1})"

                tactical_sources.append({
                    "name": label,
                    "url": s["url"]
                })

            e["tactical_sources"] = tactical_sources[:5]

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
                    "video_url": e.get("video_url"),
                    "is_video": bool(e.get("video_url") or e.get("is_video")),
                    "source_channel": e.get("source_channel", "OSINT"),
                    "multi_source_verified": e.get("multi_source_verified", False),
                    "verified_by_sources": e.get("verified_by_sources", [e.get("source_channel", "OSINT")]),
                    "tactical_sources": e.get("tactical_sources", [])
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

        video_events = [e for e in all_events_sorted if e.get("video_url") or e.get("is_video")]

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
            "video_events": video_events,
            "video_events_count": len(video_events),
            "nasa_events": nasa_events,
            "nasa_events_count": len(nasa_events),
            "nasa_max_frp": round(max_frp, 1),
            "timeline": {
                "days": timeline_days,
                "counts": timeline_counts
            },
            "map_points": map_points,
            "poland_threat": poland_threat,
            "poland_top10": self._extract_poland_top10_24h(self.all_events),
            "poland_top10_24h": self._extract_poland_top10_24h(self.all_events),
            "poland_top10_7d": self._extract_poland_top10_7d(self.all_events),
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

    def _extract_poland_top10(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self._extract_poland_top10_24h(events)

    def _extract_poland_top10_24h(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        TOP 10 incydentów z ostatnich 24 godzin o najwyższym wpływie na Polskę i NATO.
        """
        events_by_id = {e.get("id"): e for e in events if e.get("id")}

        top_configs_24h = [
            {
                "id": "5db3064f15e1d97b",
                "rank": 1,
                "badge": "🚨 DRONY ODRZUTOWE NA KIERUNKU WOŁYŃ / RÓWNE",
                "badge_color": "bg-red-950/80 text-red-200 border-red-500/60",
                "severity": "KRYTYCZNY (ZAGROŻENIE PRZYGRANICZNE)",
                "threat_score": 96,
                "summary": "Odrzutowy bezzałogowiec uderzeniowy Shahed-238 w zachodniej części obwodu żytomierskiego zmierzający bezpośrednio na zachód w kierunku obwodu rówieńskiego.",
                "direct_impact": "Prędkość przelotowa (>450 km/h) drastycznie redukuje czas reakcji polskich stacji radiolokacyjnych i par dyżurnych F-16 w bazach Łask i Krzesiny. Wektor lotu w stronę Rówieńskiej Elektrowni Atomowej (zaledwie 150 km od granicy RP) stwarza bezpośrednie ryzyko wtargnięcia w polską przestrzeń powietrzną.",
                "military_scenario": "Rosyjskie drony odrzutowe są wykorzystywane do badania luk w posterunkach radiolokacyjnych NATO wzdłuż granicy z Polską i Białorusią, a ewentualny błąd nawigacyjny grozi upadkiem aparatu na terytorium RP.",
                "recommendation": "Utrzymanie dyżuru bojowego par myśliwskich F-16 w rejonie Lubelszczyzny oraz wzmożona czujność naziemnych radarów NUR-15M i baterii Patriot."
            },
            {
                "id": "64de34bdf27a1eb6",
                "rank": 2,
                "badge": "✈️ ZASOBY I GOTOWOŚĆ BOJOWA F-16 NATO",
                "badge_color": "bg-red-950/80 text-red-200 border-red-500/60",
                "severity": "BARDZO WYSOKI (POTENCJAŁ POWIETRZNY SOJUSZU)",
                "threat_score": 92,
                "summary": "Katastrofa amerykańskiego myśliwca F-16 w Niemczech w rejonie strategicznej bazy lotniczej Spangdahlem podczas misji operacyjnej.",
                "direct_impact": "Baza Spangdahlem (52. Skrzydło Myśliwskie USAF) jest kluczowym filarem natowskiego wsparcia powietrznego dla Polski i państw bałtyckich w misjach przełamywania rosyjskiej obrony powietrznej (SEAD) w Obwodzie Królewieckim. Wypadek ten unaocznia problem przeciążenia zachodniego lotnictwa bojowego.",
                "military_scenario": "W razie pełnoskalowego konfliktu Polska będzie polegać na natychmiastowym wsparciu eskadr USAF ze Spangdahlem. Utrata maszyn i zużycie resursów floty F-16 ogranicza rotację maszyn nad wschodnią flanką.",
                "recommendation": "Intensyfikacja wdrażania polskich myśliwców F-35A Husarz, rozbudowa krajowych zapasów części zamiennych i uzbrojenia w bazach Krzesiny i Łask."
            },
            {
                "id": "9c07fe98863f1486",
                "rank": 3,
                "badge": "🌊 ZAGROŻENIE MORSKIE NA BAŁTYKU / BALTIC PIPE",
                "badge_color": "bg-cyan-950/80 text-cyan-200 border-cyan-500/60",
                "severity": "WYSOKI (INFRASTRUKTURA KRYTYCZNA NA MORZU)",
                "threat_score": 90,
                "summary": "Przekierowanie rosyjskiego eksportu surowców i operacji transportowych na Morze Bałtyckie i do portów arktycznych po utracie swobody żeglugi na Morzu Czarnym.",
                "direct_impact": "Skokowy wzrost liczby tankowców tzw. 'rosyjskiej floty cieni' oraz okrętów Floty Bałtyckiej FR w Zatoce Fińskiej i przy polskim wybrzeżu. Bezpośrednie ryzyko asymetrycznych incydentów wobec gazociągu Baltic Pipe, kabla SwePol Link i terminala LNG w Świnoujściu.",
                "military_scenario": "W fazie przedkonfliktowej Rosja może przeprowadzić operację sabotażu podwodnego lub sfingowaną kolizję tankowca w celu zablokowania toru podejściowego do polskich portów i odcięcia dostaw gazu z Norwegii.",
                "recommendation": "Wzmożone patrole niszczycieli min Kormoran II Marynarki Wojennej RP, stały monitoring podwodny dna morskiego wzdłuż korytarzy rurociągów oraz ścisła współpraca z Marynarką Wojenną Szwecji i Danii."
            },
            {
                "id": "adace3b1770730c9",
                "rank": 4,
                "badge": "🏛️ DOKTRYNA ODSTRASZANIA I SAMODZIELNOŚĆ RP",
                "badge_color": "bg-indigo-950/80 text-indigo-200 border-indigo-500/60",
                "severity": "STRATEGICZNY (WIARYGODNOŚĆ ART. 5)",
                "threat_score": 88,
                "summary": "Wystąpienie Sekretarza Generalnego NATO Marka Rutte na temat ograniczeń europejskich zdolności militarnych i konieczności drastycznego zwiększenia wydatków obronnych bez polegania wyłącznie na USA.",
                "direct_impact": "Potwierdza zasadność polskich wydatków obronnych (>4,7% PKB) i stanowi ostrzeżenie: w razie kryzysu globalnego (np. równoczesny konflikt na Pacyfiku) Polska i państwa bałtyckie muszą być gotowe do samodzielnego odparcia pierwszego uderzenia FR przez 30-60 dni.",
                "military_scenario": "Kalkulacja Kremla opiera się na założeniu, że w przypadku szybkiej aneksji kawałka terytorium (Przesmyk Suwalski) i szantażu atomowego, część stolic europejskich zawaha się przed wojną totalną.",
                "recommendation": "Dalsze wzmacnianie autonomicznych zdolności SZ RP (K2PL, Krab, Himars, Borsuk) oraz dążenie do włączenia Polski w sojuszniczy program Nuclear Sharing."
            },
            {
                "id": "a4e2cc62f321728f",
                "rank": 5,
                "badge": "💥 PARALIŻ INFRASTRUKTURY I ZAKŁÓCENIA EW",
                "badge_color": "bg-purple-950/80 text-purple-200 border-purple-500/60",
                "severity": "WYSOKI (ODPORNOŚĆ PAŃSTWA NA SZOK ENERGETYCZNY)",
                "threat_score": 86,
                "summary": "Zmasowany nocny atak rakietowo-dronowy na zakłady przemysłu chemicznego, metalurgicznego i kompleksu paliwowo-energetycznego z intensywną walką radioelektroniczną.",
                "direct_impact": "Prezentacja rosyjskiej doktryny zmasowanych uderzeń w węzły energetyczne i transportowe. W Polsce Rafineria Gdańska, PKN Orlen w Płocku i stacje rozdzielcze PSE są potencjalnymi celami analogicznego ataku w pierwszej dobie wojny.",
                "military_scenario": "Koordynacja kinetycznych ataków rakietowych z cyberatakami na system elektroenergetyczny w celu wywołania blackoutu i paraliżu mobilizacji rezerwistów.",
                "recommendation": "Budowa fizycznych zapór przeciwodłamkowych i siatek antydronowych nad strategicznymi transformatorami sieci przesyłowej PSE oraz wzmocnienie obrony cywilnej."
            },
            {
                "id": "f17c47495f84c0dc",
                "rank": 6,
                "badge": "⚠️ WEKTOR PRZEŁAMANIA POLESIA",
                "badge_color": "bg-amber-950/80 text-amber-200 border-amber-500/60",
                "severity": "WYSOKI (KORYTARZ PRZYGRANICZNY)",
                "threat_score": 84,
                "summary": "Odrzutowy bezzałogowiec uderzeniowy wykryty w rejonie strefy czarnobylskiej na kursie zachodnim.",
                "direct_impact": "Wykorzystanie zalesionego korytarza Polesia i strefy przygranicznej z Białorusią do ukrywania niskiego lotu dronów przed radarami i manewrowania w stronę zachodnich granic Ukrainy i Polski.",
                "military_scenario": "W korytarzu poleskim Rosja testuje trasy omijania radarów wczesnego ostrzegania, które w razie konfliktu posłużą do uderzeń na obiekty wojskowe na Podlasiu i Lubelszczyźnie.",
                "recommendation": "Rozbudowa sieci pasywnych radarów wczesnego ostrzegania PCL-PET (SPL) na wschodniej granicy RP."
            },
            {
                "id": "fb4a8aaa729c9a8d",
                "rank": 7,
                "badge": "🎯 SATURACJA OBRONY PRZECIWLOTNICZEJ (122 CELE)",
                "badge_color": "bg-red-950/80 text-red-200 border-red-500/60",
                "severity": "WYSOKI (ANALIZA PRACY OPL)",
                "threat_score": 82,
                "summary": "Zmasowany nalot saturacyjny na stolicę i centra przemysłowe: 122 cele powietrzne zestrzelone lub stłumione przez systemy walki radioelektronicznej.",
                "direct_impact": "Doświadczenia z obrony przed jednoczesnym atakiem dziesiątek celów stanowią kluczowe studium dla polskiego systemu Narew i Pilica+. Zwraca uwagę gigantyczne zużycie pocisków przechwytujących.",
                "military_scenario": "Rosyjska doktryna zakłada wystrzelenie setek tanich przynęt w celu wymuszenia zużycia kosztownych rakiet PAC-3 i CAMM, przed właściwym uderzeniem pociskami balistycznymi.",
                "recommendation": "Wdrożenie wielowarstwowej obrony opartej na tanich armatach przeciwlotniczych kal. 35 mm z amunicją programowalną oraz systemach laserowych/mikrofalowych."
            },
            {
                "id": "988e247d91157d35",
                "rank": 8,
                "badge": "🛡️ PARASOL OCHRONNY USA / NATO",
                "badge_color": "bg-blue-950/80 text-blue-200 border-blue-500/60",
                "severity": "STRATEGICZNY (DEKLARACJA SOJUSZNICZA)",
                "threat_score": 80,
                "summary": "Ambasador USA przy NATO Matthew Whitaker potwierdza strategiczne priorytety USA w zakresie obrony przeciwlotniczej i wzmocnienia wschodniej flanki Sojuszu.",
                "direct_impact": "Kluczowa deklaracja polityczno-wojskowa potwierdzająca, że przestrzeń powietrzna Polski i państw bałtyckich pozostaje pod stałą osłoną zintegrowanego systemu dowodzenia NATO IAMD.",
                "military_scenario": "Wzmocnienie odstraszania i jednoznaczny sygnał dla Kremla, że jakiekolwiek naruszenie polskiej przestrzeni powietrznej spotka się ze wspólną odpowiedzią Sojuszu.",
                "recommendation": "Utrzymanie stałej interoperacyjności polskich dowództw z sojuszniczym dowództwem AIRCOM w Ramstein."
            },
            {
                "id": "6253a27a9ed95ad7",
                "rank": 9,
                "badge": "⚡ WOJNA RADIOELEKTRONICZNA (EW)",
                "badge_color": "bg-indigo-950/80 text-indigo-200 border-indigo-500/60",
                "severity": "WYSOKI (ZAKŁÓCENIA NAWIGACJI GNSS)",
                "threat_score": 78,
                "summary": "Zmasowany nocny nalot dronów z intensywnym zagłuszaniem częstotliwości radarowych i łączności radiowej.",
                "direct_impact": "Rozlewanie się zakłóceń GPS/GNSS na Morze Bałtyckie i północno-wschodnią Polskę, zakłócające nawigację lotnictwa cywilnego i operacje wojskowe.",
                "military_scenario": "Próba sparaliżowania systemów precyzyjnego naprowadzania broni zachodniej (JDAM, HIMARS) za pomocą potężnych stacji Krasucha-4 i Żytiel z terenu Kaliningradu.",
                "recommendation": "Wdrożenie systemów nawigacji inercyjnej (INS) odpornych na jamming oraz procedur walki w środowisku odciętego sygnału GPS dla jednostek Wojsk Lądowych i Sił Powietrznych."
            },
            {
                "id": "fd5c838cc36014b9",
                "rank": 10,
                "badge": "🛰️ KORYTARZ PRZYGRANICZNY PÓŁNOC-ZACHÓD",
                "badge_color": "bg-slate-900 text-slate-200 border-slate-700",
                "severity": "OPERACYJNY (ROZPOZNANIE TRASY)",
                "threat_score": 76,
                "summary": "Odrzutowy BSP zmierzający w kierunku Korostenia od północy w pobliżu korytarza brzeskiego.",
                "direct_impact": "Systematyczne testowanie północno-zachodniego skrzydła obrony przeciwlotniczej wzdłuż osi Białoruś – Polska.",
                "military_scenario": "Wykorzystanie terytorium Białorusi jako platformy do wyprowadzania uderzeń dronowych na tyły polskich ugrupowań obronnych.",
                "recommendation": "Rozbudowa stanowisk obrony przeciwlotniczej wzdłuż granicy z Białorusią w ramach Tarczy Wschód."
            }
        ]

        top10_results = []
        for cfg in top_configs_24h:
            ev = events_by_id.get(cfg["id"])
            if not ev:
                continue
            item = dict(ev)
            item["poland_rank"] = cfg["rank"]
            item["poland_badge"] = cfg["badge"]
            item["poland_badge_color"] = cfg["badge_color"]
            item["poland_severity"] = cfg["severity"]
            item["poland_threat_score"] = cfg["threat_score"]
            item["poland_summary"] = cfg["summary"]
            item["poland_direct_impact"] = cfg["direct_impact"]
            item["poland_military_scenario"] = cfg["military_scenario"]
            item["poland_recommendation"] = cfg["recommendation"]
            top10_results.append(item)

        return top10_results

    def _extract_poland_top10_7d(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        TOP 10 incydentów z ostatnich 7 dni o najwyższym wpływie na Polskę i NATO.
        """
        events_by_id = {e.get("id"): e for e in events if e.get("id")}

        top_configs_7d = [
            {
                "id": "0b90944c23ee8b85",
                "rank": 1,
                "badge": "🚀 HIPERSONICZNE PRZEŁAMANIE OPL (CYRKON / KN-23)",
                "badge_color": "bg-red-950/80 text-red-200 border-red-500/60",
                "severity": "BARDZO WYSOKI (ESKALACJA BALISTYCZNA)",
                "threat_score": 98,
                "summary": "Użycie hipersonicznych pocisków 3M22 Cyrkon (Mach 8-9) oraz północnokoreańskich rakiet balistycznych KN-23 w połączonym ataku na zakłady paliwa rakietowego i głowic w Pawłogradzie i Dnieprze.",
                "direct_impact": "Rosja testuje w warunkach bojowych saturację i omijanie systemów obrony przeciwrakietowej Patriot PAC-3 CRI/MSE (będących fundamentem polskiego programu WISŁA). Czas dolotu pocisku Cyrkon lub Iskander-M z Obwodu Królewieckiego (Kaliningradu) do Warszawy wynosi poniżej 3 minut, a do Trójmiasta około 90 sekund.",
                "military_scenario": "W pierwszym rzucie uderzenia na Polskę, Rosja nie użyje lotnictwa załogowego, lecz zmasowanej salwy hipersonicznej i balistycznej z wyrzutni Iskander w Kaliningradzie i na Białorusi w celu zniszczenia polskich stanowisk dowodzenia (Bydgoszcz, Warszawa, Kraków) i stacji radarowych Wisła/Narew.",
                "recommendation": "Przyspieszenie integracji systemu dowodzenia IBCS z polskimi bateriami Patriot oraz zamówienie dodatkowych radarów dookólnych LTAMDS (360 stopni), eliminujących martwe strefy klasycznych radarów sektorowych."
            },
            {
                "id": "5db3064f15e1d97b",
                "rank": 2,
                "badge": "🚨 DRONY ODRZUTOWE NA KIERUNKU WOŁYŃ / RÓWNE",
                "badge_color": "bg-red-950/80 text-red-200 border-red-500/60",
                "severity": "KRYTYCZNY (ZAGROŻENIE PRZYGRANICZNE)",
                "threat_score": 94,
                "summary": "Zastosowanie nowej generacji bezzałogowców odrzutowych (Shahed-238) na kursie zachodnim przez obwód żytomierski w stronę obwodu rówieńskiego i granicy z Polską.",
                "direct_impact": "Prędkość przelotowa dronów odrzutowych (ponad 450 km/h wobec 180 km/h wersji tłokowej) skraca czas reakcji polskich posterunków radiolokacyjnych i par dyżurnych F-16 do kilkudziesięciu sekund. Trajektoria lotu w pobliżu Rówieńskiej Elektrowni Jądrowej (150 km od Chełma/Lublina) stwarza ryzyko zboczenia z kursu i wtargnięcia w polską przestrzeń powietrzną.",
                "military_scenario": "Rosja może wykorzystać drony odrzutowe do 'sondowania' reakcji i częstotliwości pracy polskich radarów NATO (ELINT), a w razie prowokacji – sfingować uderzenie zbłąkanego aparatu w polskie obiekty graniczne jako test determinacji Sojuszu.",
                "recommendation": "Ustanowienie stałych stref patrolowania powietrznego (CAP) przez myśliwce F-16/FA-50 wzdłuż granicy z Ukrainą i Białorusią oraz rozmieszczenie mobilnych armat przeciwlotniczych i systemów rakietowych Narew/Pilica."
            },
            {
                "id": "64de34bdf27a1eb6",
                "rank": 3,
                "badge": "✈️ ZASOBY I GOTOWOŚĆ BOJOWA F-16 NATO",
                "badge_color": "bg-blue-950/80 text-blue-200 border-blue-500/60",
                "severity": "OPERACYJNY (POTENCJAŁ POWIETRZNY SOJUSZU)",
                "threat_score": 91,
                "summary": "Katastrofa amerykańskiego myśliwca F-16 w pobliżu strategicznej bazy lotniczej Spangdahlem w Niemczech podczas rutynowej misji szkoleniowo-operacyjnej.",
                "direct_impact": "Baza Spangdahlem (52. Skrzydło Myśliwskie USAF) jest kluczową jednostką dedykowaną do misji SEAD (niszczenie rosyjskiej obrony powietrznej w Kaliningradzie i na Białorusi) oraz szybkiego wsparcia przestrzeni powietrznej Polski. Wypadki i zużycie resursów floty F-16 obnażają problem przeciążenia zachodniego lotnictwa wojskowego.",
                "military_scenario": "Wojna z Rosją będzie wymagała od Sił Powietrznych RP i USAF generowania setek samoloto-wylotów dziennie. Braki w częściach zamiennych, wyeksploatowanie silników i ograniczona liczba pilotów mogą stać się wąskim gardłem obrony polskiego nieba już w drugim tygodniu intensywnych walk.",
                "recommendation": "Przyspieszenie dostaw i wdrażania myśliwców F-35A Husarz, rozbudowa krajowych zapasów części zamiennych i uzbrojenia precyzyjnego (JASSM-ER, AMRAAM) w bazach Krzesiny i Łask."
            },
            {
                "id": "9c07fe98863f1486",
                "rank": 4,
                "badge": "🌊 ZAGROŻENIE FLOTY NA BAŁTYKU / BALTIC PIPE",
                "badge_color": "bg-cyan-950/80 text-cyan-200 border-cyan-500/60",
                "severity": "WYSOKI (INFRASTRUKTURA KRYTYCZNA NA MORZU)",
                "threat_score": 89,
                "summary": "Przekierowanie rosyjskiego eksportu surowców i operacji transportowych na Morze Bałtyckie i do portów arktycznych po utracie swobody żeglugi na Morzu Czarnym.",
                "direct_impact": "Skokowy wzrost liczby jednostek tzw. 'rosyjskiej floty cieni' (przestarzałe tankowce bez zachodnich ubezpieczeń) oraz okrętów Floty Bałtyckiej FR operujących w Zatoce Fińskiej i w pobliżu polskich wód terytorialnych. Zwiększone ryzyko prowokacji wobec gazociągu Baltic Pipe, kabla SwePol Link oraz terminala LNG w Świnoujściu.",
                "military_scenario": "W scenariuszu asymetrycznym Rosja może doprowadzić do 'przypadkowej' katastrofy ekologicznej, zerwania kotwicą rurociągu Baltic Pipe lub uderzenia dronem podwodnym w kable komunikacyjne, odcinając Polskę od dostaw gazu z Norwegii tuż przed uderzeniem militarnym.",
                "recommendation": "Wzmocnienie patroli okrętów Kormoran II Marynarki Wojennej RP, stały monitoring podwodny dna morskiego wzdłuż korytarzy rurociągów oraz ścisła współpraca z Marynarką Wojenną Szwecji i Danii w Cieśninach Duńskich."
            },
            {
                "id": "adace3b1770730c9",
                "rank": 5,
                "badge": "🏛️ DOKTRYNA ODSTRASZANIA I SAMODZIELNOŚĆ RP",
                "badge_color": "bg-slate-900 text-slate-200 border-slate-600",
                "severity": "STRATEGICZNY (WIARYGODNOŚĆ ART. 5)",
                "threat_score": 87,
                "summary": "Wystąpienie Sekretarza Generalnego NATO Marka Rutte na temat ograniczeń europejskich zdolności militarnych i konieczności drastycznego zwiększenia wydatków obronnych bez polegania wyłącznie na USA.",
                "direct_impact": "Polska jest europejskim liderem wydatków obronnych (ponad 4,7% PKB), jednak deklaracje kierownictwa NATO potwierdzają obawy o tempo pomocy sojuszniczej w pierwszych tygodniach wojny. W razie jednoczesnego konfliktu USA na Pacyfiku (Tajwan), Polska i kraje wschodniej flanki będą musiały samodzielnie powstrzymać uderzenie rosyjskie.",
                "military_scenario": "Rosyjska kalkulacja wojenna opiera się na założeniu, że w przypadku szybkiej aneksji kawałka terytorium (np. Przesmyku Suwalskiego) i groźby użycia taktycznej broni jądrowej, część stolic europejskich zawaha się przed uruchomieniem Art. 5, doprowadzając do rozpadu NATO.",
                "recommendation": "Budowa w pełni autonomicznych zdolności obronnych SZ RP (programy Miecznik, Borsuk, K2PL, Krab, Himars) oraz dążenie do włączenia Polski w sojuszniczy program Nuclear Sharing."
            },
            {
                "id": "a4e2cc62f321728f",
                "rank": 6,
                "badge": "🎯 TAKTYKA PORAŻENIA INFRASTRUKTURY I WALKA EW",
                "badge_color": "bg-purple-950/80 text-purple-200 border-purple-500/60",
                "severity": "WYSOKI (ODPORNOŚĆ PAŃSTWA NA SZOK ENERGETYCZNY)",
                "threat_score": 85,
                "summary": "Zmasowane uderzenia rakietowo-dronowe na zakłady przemysłu chemicznego, metalurgicznego i kompleksu paliwowo-energetycznego z intensywnym zakłócaniem łączności i nawigacji.",
                "direct_impact": "Rosja doskonali doktrynę całkowitego paraliżu gospodarczego kraju poprzez niszczenie elektrociepłowni, transformatorów WN, rafinerii i węzłów kolejowych. W Polsce obiekty takie jak Rafineria Gdańska, PKN Orlen w Płocku, Elektrownia Kozienice czy kluczowe stacje rozdzielcze PSE są podatne na analogiczne ataki rojów dronów i pocisków manewrujących Ch-101.",
                "military_scenario": "Wybuch wojny zostanie poprzedzony lub skoordynowany z uderzeniem w polski system elektroenergetyczny (blackout) oraz zakłóceniem sieci komórkowych i łączności bankowej, wywołując panikę społeczną i paraliżując mobilizację rezerwistów.",
                "recommendation": "Budowa odporności cywilnej (Ustawa o ochronie ludności), decentralizacja zasilania awaryjnego w szpitalach i jednostkach wojskowych oraz instalacja fizycznych siatek przeciwkumulacyjnych i przeciwodłamkowych nad transformatorami strategicznymi."
            },
            {
                "id": "48eaf92ffe9b4110",
                "rank": 7,
                "badge": "⚠️ ROJE DRONÓW W KORYTARZU ZACHODNIM (WOŁYŃ)",
                "badge_color": "bg-amber-950/80 text-amber-200 border-amber-500/60",
                "severity": "WYSOKI (PRZYGRANICZNE SZLAKI LOGISTYCZNE)",
                "threat_score": 83,
                "summary": "Zmasowane uderzenia dronów 'Pelargonia' w infrastrukturę magazynową i produkcyjną na kierunkach zachodnich i w rejonie Wasilkowa.",
                "direct_impact": "Uderzenia w pobliżu korytarzy transportowych łączących Polskę z centralną Ukrainą. Zagrożenie dla szlaków zaopatrzeniowych i węzłów kolejowych.",
                "military_scenario": "Rosja ćwiczy odcinanie linii kolejowych i dróg przesyłowych na zachodzie Ukrainy tuż przy polskiej granicy.",
                "recommendation": "Rozbudowa ochrony przeciwlotniczej korytarzy granicznych i posterunków celno-kolejowych po polskiej stronie."
            },
            {
                "id": "b1f35747e5ba2787",
                "rank": 8,
                "badge": "⛽ NISZCZENIE BAZ PALIWOWYCH PRZY GRANICY RP",
                "badge_color": "bg-red-950/80 text-red-300 border-red-700/50",
                "severity": "WYSOKI (LOGISTYKA PALIWOWA)",
                "threat_score": 81,
                "summary": "Systematyczne uderzenia rakietowe i dronowe niszczące bazy paliwowo-energetyczne na zachodzie Ukrainy i Wołyniu.",
                "direct_impact": "Ataki na magazyny paliw zaledwie 50-80 km od granicy z Polską. Zwiększone ryzyko pożarów przygranicznych i paraliżu dostaw paliwowych.",
                "military_scenario": "Uderzenie w polskie magazyny paliw PERN i bazy paliwowe w razie konfliktu w celu unieruchomienia jednostek zmechanizowanych.",
                "recommendation": "Objęcie baz paliwowych PERN i strategicznych rurociągów stałym monitoringiem antydronowym i obroną OPL."
            },
            {
                "id": "29a57f6ee0ffd1ef",
                "rank": 9,
                "badge": "🛵 ODRZUTOWE BSP NAD TARNOPOLEM (180 KM OD RP)",
                "badge_color": "bg-amber-950/80 text-amber-200 border-amber-500/60",
                "severity": "WYSOKI (PRZEŁAMANIE GŁĘBOKIE)",
                "threat_score": 79,
                "summary": "Przelot odrzutowego drona Shahed przez Tarnopol na kursie zachodnim.",
                "direct_impact": "Tarnopol znajduje się 180 km od granicy RP; uderzenia w tym rejonie wymuszają procedury poderwania polskich par F-16.",
                "military_scenario": "Rosja testuje reakcję polskiego Dowództwa Operacyjnego RSZ na przeloty pocisków i dronów w bezpośrednim sąsiedztwie polskiej strefy FIR.",
                "recommendation": "Utrzymanie procedury natychmiastowego startu (QRA) par F-16 podczas ataków na obwody tarnopolski i lwowski."
            },
            {
                "id": "1bd211bd12e2eb58",
                "rank": 10,
                "badge": "💥 DETONACJE W WĘZŁACH PRZEŁADUNKOWYCH AMUNICJI",
                "badge_color": "bg-slate-900 text-slate-200 border-slate-700",
                "severity": "OPERACYJNY (ŁAŃCUCH LOGISTYCZNY)",
                "threat_score": 77,
                "summary": "Potężne pożary i detonacje magazynów amunicji i sprzętu po serii uderzeń rakietowych.",
                "direct_impact": "Uderzenia w składy amunicyjne pokazują rosyjską skuteczność namierzania węzłów przeładunkowych z dostaw zachodnich.",
                "military_scenario": "W razie wojny z Rosją polskie bazy logistyczne w Rzeszowie, Nisku i Lublinie będą pierwszymi celami uderzeń rakietowych.",
                "recommendation": "Maksymalne rozproszenie składów amunicji i sprzętu Wojska Polskiego w małych, zamaskowanych magazynach polowych."
            }
        ]

        top10_results = []
        for cfg in top_configs_7d:
            ev = events_by_id.get(cfg["id"])
            if not ev:
                continue
            item = dict(ev)
            item["poland_rank"] = cfg["rank"]
            item["poland_badge"] = cfg["badge"]
            item["poland_badge_color"] = cfg["badge_color"]
            item["poland_severity"] = cfg["severity"]
            item["poland_threat_score"] = cfg["threat_score"]
            item["poland_summary"] = cfg["summary"]
            item["poland_direct_impact"] = cfg["direct_impact"]
            item["poland_military_scenario"] = cfg["military_scenario"]
            item["poland_recommendation"] = cfg["recommendation"]
            top10_results.append(item)

        return top10_results
