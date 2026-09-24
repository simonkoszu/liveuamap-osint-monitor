#!/usr/bin/env bash
# Aegis OSINT Tactical Radar - Błyskawiczny wyzwalacz skanu chmurowego
# Odpala workflow na GitHub Actions bez wchodzenia do przeglądarki!

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "🛡️ AEGIS OSINT RADAR - ZDALNE WYWOŁANIE SKANU CHMUROWEGO"
echo "============================================================"

# Metoda 1: Jeśli GitHub CLI (gh) jest zalogowany
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    echo "📡 Wykryto autoryzację GitHub CLI (gh)..."
    echo "🚀 Uruchamianie workflow 'update_report.yml'..."
    gh workflow run update_report.yml --ref main
    echo "✅ Zlecenie przyjęte przez GitHub Actions!"
    echo "⏳ Podgląd na żywo możesz śledzić poleceniem: gh run watch"
    exit 0
fi

# Metoda 2: Bezpośredni Git Push (wyzwala workflow na gałęzi main)
echo "🚀 Wysyłanie zdalnego sygnału wyzwalającego przez Git Push..."
git commit --allow-empty -m "Remote trigger: Aegis OSINT Radar Scan [$(date -u +'%Y-%m-%d %H:%M UTC')]"
git push origin main

echo "============================================================"
echo "✅ SUKCES! Skan wystartował na serwerach GitHub Actions."
echo "⏱️ Przetwarzanie i publikacja zajmie około 2 minuty."
echo "🌐 Gotowy raport: https://simonkoszu.github.io/liveuamap-osint-monitor/"
echo "============================================================"
