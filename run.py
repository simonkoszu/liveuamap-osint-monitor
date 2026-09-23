#!/usr/bin/env python3
import os
import sys
import argparse

# Dodaj katalog src do sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from database import EventDatabase
from scraper import AegisOSINTScraper
from analyzer import ConflictAnalyzer
from generator import ReportGenerator
from enricher import enrich_database
from nlp_engine import MilitaryNLPEngine

def main():
    parser = argparse.ArgumentParser(description="Aegis OSINT Tactical Radar - Global Intelligence Monitor")
    parser.add_argument("--pages", type=int, default=5, help="Liczba stron historii do pobrania (domyślnie 5)")
    parser.add_argument("--no-scrape", action="store_true", help="Pomiń scraping i użyj istniejącej bazy danych")
    parser.add_argument("--desktop-folder", type=str, default="aegis_osint_raport", help="Nazwa folderu na Pulpicie")
    args = parser.parse_args()

    print("=" * 60)
    print("🛡️ AEGIS OSINT TACTICAL RADAR - CYKL OPERACYJNY")
    print("=" * 60)

    db_path = os.path.join(BASE_DIR, "data", "events.json")
    templates_dir = os.path.join(BASE_DIR, "templates")
    output_dir = os.path.join(BASE_DIR, "output")

    # 1. Baza danych
    db = EventDatabase(db_path)
    print(f"📦 Baza wywiadowcza załadowana: {len(db.events)} zarejestrowanych incydentów.")

    # 2. Scraping zdarzeń
    if not args.no_scrape:
        print(f"📡 Pobieranie najnowszych meldunków radarowych (strony: {args.pages})...")
        scraper = AegisOSINTScraper()
        new_events = scraper.fetch_latest_events(max_pages=args.pages)
        added_count = 0
        for ev in new_events:
            if db.add_event(ev):
                added_count += 1
        db.save()
        print(f"✅ Zarejestrowano {added_count} nowych meldunków. Łącznie w buforze: {len(db.events)}.")
    else:
        print("⏩ Pominięto scraping, przetwarzanie bazy danych.")

    # 2b. Wzbogacenie o zweryfikowane incydenty
    enrich_database(db)

    # 2c. Telemetria satelitarna NASA FIRMS (jeśli skonfigurowano MAP_KEY)
    try:
        from nasa_firms import fetch_nasa_firms_hotspots
        firms_events = fetch_nasa_firms_hotspots()
        if firms_events:
            added_firms = sum(1 for ev in firms_events if db.add_event(ev))
            print(f"🛰️ Dodano {added_firms} nowych anomalii satelitarnych NASA FIRMS do bazy.")
            db.save()
    except Exception as e:
        print(f"ℹ️ [NASA FIRMS] Pominięto pobieranie satelitarne: {e}")

    # 3. Analiza statystyczna, redukcja szumów i deduplikacja
    print("🧠 Analiza danych, redukcja szumów i inteligentna deduplikacja...")
    all_events = db.get_all_events()

    # Oczyszczanie bazy: eliminacja spamu, szumu lifestyle i zdarzeń niemilitarnych
    military_events = []
    purged_count = 0
    for ev in all_events:
        raw_text = (ev.get("text") or "") + " " + (ev.get("title") or "")
        if MilitaryNLPEngine.is_military_event(raw_text):
            military_events.append(ev)
        else:
            purged_count += 1
    if purged_count > 0:
        print(f"   🧹 Filtr Antyszumowy: usunięto {purged_count} niemilitarnych wpisów tabloidowych/spamu z bazy.")
        all_events = military_events

    # Inteligentne łączenie duplikatów z wielu kanałów
    deduplicated_events, merged_count = MilitaryNLPEngine.deduplicate_and_merge_events(all_events)
    print(f"   • Inteligentna deduplikacja: scalono {merged_count} zdublowanych raportów w unikalne zdarzenia wieloźródłowe.")

    # Cross-referencing i weryfikacja
    deduplicated_events = MilitaryNLPEngine.cross_verify_events(deduplicated_events)

    # 2d. Tłumaczenie incydentów na język polski (z buforowaniem)
    from translator import translate_events_batch
    translate_events_batch(deduplicated_events, max_to_translate=1000)

    db.events = {ev["id"]: ev for ev in deduplicated_events}
    db.save()

    analyzer = ConflictAnalyzer(deduplicated_events, tracking_started_at=db.meta.get("tracking_started_at"))
    analysis = analyzer.analyze()

    print(f"   • Aktywne unikalne incydenty po deduplikacji: {analysis['total_events_in_db']}")
    print(f"   • Ostatnie 24h (Globalnie): {analysis['global_daily']['count']} zdarzeń")
    print(f"   • Potwierdzone Wieloźródłowo (Cross-Check): {analysis['multi_source_verified_count']} zdarzeń")
    print("   • Rozkład wg Taksonomii Bojowej:")
    for cat, cnt in list(analysis.get('tactical_categories', {}).items())[:6]:
        print(f"     - {cat}: {cnt}")
    print("   • Podział na kraje:")
    for c in analysis['countries']:
        if c['total_events'] > 0:
            print(f"     - {c['flag']} {c['name']}: {c['total_events']} zdarzeń (24h: {c['daily']['count']}, 7d: {c['weekly']['count']})")

    pt = analysis.get("poland_threat", {})
    if pt:
        print("=" * 60)
        print(f"⏱️ ZEGAR ZAGROŻENIA WOJNĄ POLSKI Z ROSJĄ (NATO): {pt.get('threat_clock_time')} (Za {pt.get('minutes_to_midnight')} min do północy)")
        print(f"   • Status: {pt.get('threat_level')} [{pt.get('defcon_equivalent')}]")
        print(f"   • Wskaźnik Ryzyka Łącznego: {pt.get('threat_index')}/100 | Trend: {pt.get('trend')}")
        if pt.get("alerts"):
            print(f"   🚨 Aktywne Alerty Wczesnego Ostrzegania ({len(pt['alerts'])}):")
            for al in pt["alerts"]:
                print(f"      [{al.get('badge')}] {al.get('title')}")
        print("=" * 60)

    # 4. Generowanie raportu HTML
    print("🎨 Renderowanie interaktywnego panelu taktycznego Aegis Radar...")
    generator = ReportGenerator(templates_dir, output_dir)
    report_path = generator.generate(analysis, desktop_folder_name=args.desktop_folder)

    # Zapisz również pod dawną nazwą na Pulpicie dla wygody użytkownika
    try:
        legacy_dir = os.path.expanduser("~/Desktop/liveuamap_raport")
        if os.path.exists(legacy_dir):
            import shutil
            shutil.copyfile(report_path, os.path.join(legacy_dir, "index.html"))
    except Exception:
        pass

    print("=" * 60)
    print(f"🎉 SUKCES! Raport Aegis Radar jest gotowy:")
    print(f"   Projekt: {report_path}")
    print(f"   Pulpit:  ~/Desktop/{args.desktop_folder}/index.html")
    print("=" * 60)

if __name__ == "__main__":
    main()
