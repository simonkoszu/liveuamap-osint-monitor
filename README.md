# 🛰️ Liveuamap War Monitor & Cloud Reporter

W pełni zautomatyzowany, **100% bezpłatny i bezpieczny** system monitorowania konfliktów zbrojnych i wojen na bazie **liveuamap.com**. Generuje interaktywne raporty w HTML z podziałem na poszczególne kraje, śledzi dynamikę zmian od dnia dzisiejszego oraz wizualizuje ogniska zapalne na mapie operacyjnej.

---

## 🛡️ Dlaczego to rozwiązanie jest w 100% bezpieczne?

1. **Architektura Zero Inbound Ports (Brak otwartych portów)**:
   - Program **nie stawia serwera** (ani VPS, ani Flask, ani Node.js).
   - Skrypt uruchamia się w chmurze **GitHub Actions** w odizolowanej mikro-maszynie wirtualnej (ephemeral VM), pobiera dane przez bezpieczne, wychodzące zapytania HTTPS (egress-only) i natychmiast ulega samozniszczeniu.
   - **Nikt nie może się "wbić"**, ponieważ pod adresem raportu nie ma żadnego otwartego portu sieciowego ani podatnego kodu backendowego.
2. **Statyczny HTML**:
   - Raport jest czystym plikiem HTML/JS bez bazy SQL w internecie (brak SQL Injection) i bez PHP/Pythona po stronie serwera WWW (brak RCE).
3. **Ochrona przed XSS i Restrykcyjne CSP**:
   - Wszystkie teksty i linki ze źródeł zewnętrznych są sanityzowane i uciekane znakowo (`autoescape=True`).
   - W nagłówkach raportu zaszyta jest polityka `Content-Security-Policy`.

---

## 🌍 Co zawiera raport?

### 1. Rozbicie na poszczególne państwa (Country Breakdown)
Każdy kraj i teatr działań posiada własny, dedykowany panel:
* 🇺🇦 **Ukraina** (Front wschodni, uderzenia rakietowe, obwody doniecki, charkowski, zaporoski itp.)
* 🇱🇧 **Liban** (Południowy Liban, Bejrut, Dahieh, ostrzały graniczne)
* 🇵🇸 🇮🇱 **Izrael i Palestyna** (Strefa Gazy: Rafah, Chan Junus, Dżabalija oraz Zachodni Brzeg)
* 🇸🇾 **Syria** (Damaszek, Aleppo, Idlib, naloty i incydenty zbrojne)
* 🇾🇪 **Jemen i Morze Czerwone** (Huti, ataki na szlaki żeglugowe, naloty koalicji)
* 🇸🇩 **Sudan** (Chartum, Darfur, Al-Faszir - starcia SAF i RSF)
* 🇷🇺 **Rosja** (Uderzenia w głąb terytorium FR, obwody kurski, biełgorodzki)

### 2. Raporty Czasowe
Dla każdego kraju oraz globalnie:
* **Raport Dzienny (24h)**: Ostatnia doba, wskaźnik dynamiki vs poprzednie 24h (+/- %), ogniska zapalne, charakter incydentów.
* **Raport Tygodniowy (7 dni)**: Ostatnie 7 dni, struktura broni i uderzeń, zmiana tydzień do tygodnia.
* **Raport Miesięczny (30 dni)**: Bilans strategiczny, skumulowana liczba incydentów.
* **Śledzenie zmian od dnia dzisiejszego**: Licznik i baza zdarzeń rejestrująca każdą nową zmianę na mapie od startu monitora.

### 3. Interaktywna Mapa Operacyjna (Leaflet.js)
* Ciemny motyw OSINT (CartoDB Dark).
* Kolorowe oznaczenia incydentów dopasowane do państw.
* Filtrowanie jednym kliknięciem: np. tylko Ukraina, tylko Liban, tylko Bliski Wschód.
* Klikalne punkty z pełnym opisem zdarzenia, godziną i bezpośrednim linkiem do Liveuamap.

---

## 🚀 Jak uruchomić w darmowej chmurze (GitHub Actions + Pages)

Całość jest przystosowana do darmowej infrastruktury GitHub (0 zł, bez karty kredytowej).

### Krok 1: Utwórz prywatne repozytorium na GitHubie
1. Wejdź na [github.com/new](https://github.com/new).
2. Nazwij repozytorium np. `liveuamap-war-reporter`.
3. Zaznacz **Private** (dla pełnej dyskrecji) lub Public.
4. Kliknij **Create repository**.

### Krok 2: Wypchnij kod do repozytorium
W terminalu w katalogu `liveuamap_cloud`:
```bash
cd liveuamap_cloud
git init
git add .
git commit -m "Inicjalizacja bezpiecznego monitora Liveuamap"
git branch -M main
git remote add origin https://github.com/TWOJ_LOGIN/liveuamap-war-reporter.git
git push -u origin main
```

### Krok 3: Włącz darmowy hosting GitHub Pages
1. W repozytorium na GitHub wejdź w **Settings** -> **Pages**.
2. W sekcji **Build and deployment** zmień **Source** na:
   👉 **GitHub Actions**.
3. To wszystko! GitHub Actions automatycznie:
   - Odpala scraping i analizę 2 razy dziennie (06:00 i 18:00 UTC) w chmurze,
   - Zapisuje nowe zdarzenia do bazy `data/events.json`,
   - Publikuje najświeższy raport HTML pod Twoim prywatnym linkiem GitHub Pages.
   - Możesz też uruchomić raport w dowolnym momencie ręcznie: zakładka **Actions** -> **Aktualizacja Raportu Wojennego Liveuamap** -> **Run workflow**.

---

## 💻 Uruchamianie lokalne na komputerze

Skrypt automatycznie generuje raport i **zapisuje kopię bezpośrednio na Twoim Pulpicie**:

```bash
# Uruchomienie pełnego cyklu (pobranie danych + analiza + raport):
python3 run.py --pages 5

# Otwarcie wygenerowanego raportu z Pulpitu:
open ~/Desktop/liveuamap_raport/index.html
```
Raport otworzy się natychmiast w Twojej domyślnej przeglądarce internetowej.
