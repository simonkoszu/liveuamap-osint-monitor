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
    "Inne / Globalne": {"flag": "🌐", "theater": "Inne", "priority": 9},
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
                "recent_events": ev_list[:10]
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

        for e in self.all_events[:600]:
            lat = e.get("lat")
            lon = e.get("lon")
            if lat and lon:
                c = e.get("country", "Inne")
                text = e.get("text", "")
                weapons = MilitaryNLPEngine.extract_weapons(text)
                target = MilitaryNLPEngine.extract_target_type(text)
                has_fire = MilitaryNLPEngine.detect_fire_or_thermal(text)
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
                    "url": e.get("url"),
                    "weapons": weapons,
                    "target_type": target,
                    "has_fire": has_fire,
                    "threat_score": threat,
                    "source_channel": e.get("source_channel", "OSINT"),
                    "multi_source_verified": e.get("multi_source_verified", False),
                    "verified_by_sources": e.get("verified_by_sources", [e.get("source_channel", "OSINT")])
                })

        import hashlib
        import os
        auth_salt = "aegis_tactical_salt_2026_osint"
        report_pin = os.getenv("REPORT_PIN", "7749").strip() or "7749"
        auth_hash = hashlib.sha256((auth_salt + report_pin).encode("utf-8")).hexdigest()
        carto_api_key = os.getenv("CARTO_API_KEY", "").strip() or "cb1_3u7r_1_3c8d42e4911c679a2d091c0d"

        return {
            "generated_at": self.now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "today_date": self.now.strftime("%Y-%m-%d"),
            "total_events_in_db": len(self.all_events),
            "events_today_count": len(all_today),
            "multi_source_verified_count": verified_count,
            "tactical_categories": dict(tactical_counts.most_common()),
            "global_daily": self._calculate_period_stats(all_24h, all_prev_24h),
            "global_weekly": self._calculate_period_stats(all_7d, all_prev_7d),
            "global_monthly": self._calculate_period_stats(all_30d, all_prev_30d),
            "countries": countries_report,
            "timeline": {
                "days": timeline_days,
                "counts": timeline_counts
            },
            "map_points": map_points,
            "auth_salt": auth_salt,
            "auth_hash": auth_hash,
            "carto_api_key": carto_api_key
        }
