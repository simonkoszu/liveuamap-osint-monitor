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
from scraper import LiveuamapScraper
from analyzer import ConflictAnalyzer
from generator import ReportGenerator
from enricher import enrich_database
from nlp_engine import MilitaryNLPEngine

def main():
    parser = argparse.ArgumentParser(description="Liveuamap War Reporter - OSINT Cloud Monitor")
    parser.add_argument("--pages", type=int, default=5, help="Liczba stron historii do pobrania (domyślnie 5)")
    parser.add_argument("--no-scrape", action="store_true", help="Pomiń scraping i użyj istniejącej bazy danych")
    parser.add_argument("--desktop-folder", type=str, default="liveuamap_raport", help="Nazwa folderu na Pulpicie")
    args = parser.parse_args()

    print("=" * 60)
    print("🚀 LIVEUAMAP CLOUD REPORTER - ROZPOCZĘCIE CYKLU OPERACYJNEGO")
    print("=" * 60)

    db_path = os.path.join(BASE_DIR, "data", "events.json")
    templates_dir = os.path.join(BASE_DIR, "templates")
    output_dir = os.path.join(BASE_DIR, "output")

    # 1. Baza danych
    db = EventDatabase(db_path)
    print(f"📦 Baza danych załadowana: {len(db.events)} zarejestrowanych zdarzeń.")

    # 2. Scraping zdarzeń
    if not args.no_scrape:
        print(f"📡 Pobieranie najnowszych zdarzeń z Liveuamap (strony: {args.pages})...")
        scraper = LiveuamapScraper()
        new_events = scraper.fetch_latest_events(max_pages=args.pages)
        added_count = 0
        for ev in new_events:
            if db.add_event(ev):
                added_count += 1
        db.save()
        print(f"✅ Dodano {added_count} nowych incydentów do bazy. Łącznie w bazie: {len(db.events)}.")
    else:
        print("⏩ Pominięto scraping, używanie istniejącej bazy.")

    # 2b. Wzbogacenie o zweryfikowane incydenty ze wszystkich teatrów i krajów (w tym Rosja/Samara)
    enrich_database(db)

    # 3. Analiza statystyczna (dzienna, tygodniowa, miesięczna, od dzisiaj)
    print("🧠 Analiza danych, redukcja szumów i weryfikacja krzyżowa (Cross-Check)...")
    all_events = db.get_all_events()
    all_events = MilitaryNLPEngine.cross_verify_events(all_events)
    for ev in all_events:
        db.events[ev["id"]] = ev
    db.save()

    analyzer = ConflictAnalyzer(all_events, tracking_started_at=db.meta.get("tracking_started_at"))
    analysis = analyzer.analyze()

    print(f"   • Ostatnie 24h (Globalnie): {analysis['global_daily']['count']} zdarzeń (zmiana: {analysis['global_daily']['diff']:+d})")
    print(f"   • Ostatnie 7 dni (Globalnie): {analysis['global_weekly']['count']} zdarzeń (zmiana: {analysis['global_weekly']['diff']:+d})")
    print(f"   • Ostatnie 30 dni (Globalnie): {analysis['global_monthly']['count']} zdarzeń")
    print(f"   • Śledzenie od dzisiaj ({analysis['today_date']}): {analysis['events_today_count']} zdarzeń")
    print(f"   • Potwierdzone Wieloźródłowo (Cross-Check): {analysis['multi_source_verified_count']} zdarzeń")
    print("   • Podział na kraje:")
    for c in analysis['countries']:
        if c['total_events'] > 0:
            print(f"     - {c['flag']} {c['name']}: {c['total_events']} zdarzeń (24h: {c['daily']['count']}, 7d: {c['weekly']['count']}, 30d: {c['monthly']['count']})")

    # 4. Generowanie raportu HTML
    print("🎨 Renderowanie interaktywnego raportu HTML (Leaflet + Chart.js)...")
    generator = ReportGenerator(templates_dir, output_dir)
    report_path = generator.generate(analysis, desktop_folder_name=args.desktop_folder)

    print("=" * 60)
    print(f"🎉 SUKCES! Raport jest gotowy do otwarcia:")
    print(f"   Projekt: {report_path}")
    print(f"   Pulpit:  ~/Desktop/{args.desktop_folder}/index.html")
    print("=" * 60)

if __name__ == "__main__":
    main()
