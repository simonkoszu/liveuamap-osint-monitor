# 🏛️ Aegis OSINT Radar - Długoterminowa Baza Historyczna & Zbiór Danych ML

Ten katalog zawiera zarchiwizowane zdarzenia wywiadowcze starsze niż 14 dni, wycofane z aktywnego radaru operacyjnego, aby zachować wysoką wydajność interfejsu i lekkość bazy operacyjnej.

## 📦 Pliki w Katalogu

1. **`historical_dataset.jsonl`** *(Format JSON Lines)*:
   - Każda linijka to kompletny obiekt JSON reprezentujący jedno zdarzenie wojskowe.
   - **Zastosowanie w AI / ML**:
     - Fine-tuning modeli językowych (LLM) pod terminologię wojskową i rozpoznawanie broni.
     - Analizy czasowo-przestrzenne (Geospatial Analysis) w Pythonie: `pd.read_json("historical_dataset.jsonl", lines=True)`.
     - Ładowanie do baz wektorowych (RAG) i hurtowni danych (Google BigQuery, DuckDB, ClickHouse).
     - Trenowanie klasyfikatorów eskalacji (Threat Score 1-10) i detekcji broni.

2. **`events_archive.json`**:
   - Kompletny zrzut słownikowy z metadanymi i indeksem identyfikatorów zdarzeń (`id`).

3. **`archive_manifest.json`**:
   - Statystyki archiwalne: liczba zarchiwizowanych rekordów, data najstarszego i najnowszego wpisu, status synchronizacji chmurowej.

4. **`google_apps_script.js`**:
   - Darmowy skrypt Google Apps Script do automatycznego przesyłania kopii zapasowych na Twój Dysk Google (Google Drive).

## ☁️ Integracja z Dyskiem Google (Opcjonalna)

Aby archiwum automatycznie lądowało na Twoim Dysku Google:
1. Skopiuj kod z pliku `google_apps_script.js`.
2. Wklej go na https://script.google.com/ i wdróż jako **Web App** (Aplikację internetową).
3. Dodaj wygenerowany URL do GitHub Secrets w repozytorium jako:
   `GDRIVE_WEBHOOK_URL = https://script.google.com/macros/s/.../exec`
