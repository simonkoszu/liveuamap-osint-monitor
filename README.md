# 🛰️ Aegis Tactical OSINT Radar & War Monitor

Autonomiczny, **100% bezpłatny i utwardzony kryptograficznie** system wywiadu otwartoźródłowego (OSINT) do monitorowania konfliktów zbrojnych i teatrów wojennych na świecie.

Agreguje zdarzenia wielokanałowo, wykonuje **fuzję i deduplikację czasowo-przestrzenną (spatial-temporal clustering)**, klasyfikuje incydenty do 9 precyzyjnych kategorii taktycznych oraz chroni interaktywny pulpit operacyjny za **kryptograficzną bramką PIN (SHA-256)**.

---

## 🔐 Zabezpieczenia Kryptograficzne i Ochrona przed Atakami

1. **Bramka Bezpieczeństwa PIN (SHA-256)**:
   - Dashboard jest całkowicie zablokowany do momentu wprowadzenia prawidłowego 4-cyfrowego kodu PIN (Domyślny PIN: **`7749`**).
   - Hasło nie występuje w kodzie źródłowym w formie jawnej – weryfikacja następuje w standardzie **SHA-256** przy użyciu Web Crypto API.
   - **Ochrona Anty-Bruteforce**: Po 3 błędnych próbach interfejs blokuje wprowadzanie kodu na 10 sekund.
   - Posiada szybki przycisk natychmiastowego ryglowania ekranu (**Zablokuj**).

2. **Architektura Zero Inbound Ports (Brak otwartych portów)**:
   - System nie utrzymuje żadnego otwartego serwera HTTP, VPS, Flask czy Node.js.
   - Weryfikacja i kompilacja danych odbywa się w odizolowanym środowisku chmury **GitHub Actions** (ephemeral runner), a wynik jest publikowany jako statyczny, zaszyfrowany pulpit.
   - Nie istnieje żaden port ani usługa sieciowa podatna na skanery portów, exploity czy ataki DDoS/RCE.

3. **Restrykcyjne CSP i Sanityzacja Danych**:
   - Wszystkie nagłówki zawierają ścisłą politykę `Content-Security-Policy`.
   - Zabezpieczenie przed XSS (`autoescape=True`) w szablonach Jinja2.

---

## 🎯 Silnik Taktyczny & Deduplikacja Zdarzeń

### 1. Fuzja i Deduplikacja Czasowo-Przestrzenna
Gdy wiele kanałów OSINT, radarów i korespondentów wojennych donosi o tym samym ataku (np. uderzenie w rafinerię w Samarze lub zakład przemysłowy w Dnieprze):
- Algorytm grupuje incydenty w promieniu **< 25 km** i oknie czasowym **< 12 godzin**.
- Tworzy pojedynczy, kanoniczny wpis oznaczony tarczą: **`🛡️ Cross-Check`** z listą wszystkich niezależnych źródeł, które potwierdziły zdarzenie.

### 2. Precyzyjna Taksonomia Wojskowa (9 Kategorii)
Każdy incydent analizowany jest pod kątem sygnatury taktycznej:
- 💥 **Eksplozje & Ostrzał Artyleryjski** (detonacje, GRAD, MLRS, artyleria lufowa)
- 🛸 **Ataki Dronów Kamikaze** (Shahed-136, Geran, FPV, Lancet)
- 🚀 **Uderzenia Balistyczne i Manewrujące** (Iskander, Kalibr, Kinżał, Ch-101, ATACMS)
- 💣 **Bomby Lotnicze KAB / FAB** (korygowane bomby lotnicze z modułami UMPC)
- 🏭 **Infrastruktura Krytyczna i Paliwowa** (rafinerie, składy ropy, elektrociepłownie, transformatory)
- ⚔️ **Szturmy Lądowe & Przełamania Frontu** (starcia piechoty, natarcia pancerne)
- 🛡️ **Obrona Powietrzna & Zestrzelenia** (przechwycenia Patriot, NASAMS, S-400)
- ⚓ **Operacje Morskie & Drony Nawodne** (Magura V5, incydenty na Morzu Czarnym/Czerwonym)
- 📢 **Komunikaty Sztabowe & Deklaracje** (raporty Sztabu Generalnego, ISW, ministerstw obrony)

---

## 🌍 Teatry Działań Wojennych

Dedykowane panele analityczne i raporty wielookresowe (**24h dzienny**, **7d tygodniowy**, **30d miesięczny**, **zmiany skumulowane**):
* 🇺🇦 **Ukraina** (Front wschodni, Pokrowsk, Torećk, Kupiańsk, obrona powietrzna, uderzenia w infrastrukturę)
* 🇷🇺 **Rosja** (Uderzenia w głąb terytorium FR, rafinerie ropy naftowej, obwody kurski, biełgorodzki, bazy lotnicze)
* 🇱🇧 **Liban** (Południowy Liban, Bejrut, Dahieh, ostrzały graniczne)
* 🇵🇸 🇮🇱 **Izrael i Palestyna** (Strefa Gazy oraz Zachodni Brzeg)
* 🇸🇾 **Syria** (Damaszek, Hama, Aleppo, Idlib, naloty i incydenty zbrojne)
* 🇾🇪 **Jemen i Morze Czerwone** (Huti, szlaki żeglugowe Bab al-Mandab)
* 🇸🇩 **Sudan** (Chartum, Darfur, Al-Faszir - starcia SAF i RSF)

---

## 📡 Rejestr Aktywnych Źródeł Danych Wywiadowczych (Sensors & Feeds)

System autonomicznie agreguje zdarzenia w czasie rzeczywistym, filtruje antyszumowo przy użyciu dedykowanych reguł NLP oraz dokonuje fuzji wieloźródłowej z następujących kanałów:

| Źródło / Identyfikator | Typ / Protokół | Obszar / Teatr Działań | Główny Cel Operacyjny | Status |
| :--- | :--- | :--- | :--- | :--- |
| [**Defence24**](https://defence24.pl) | RSS (`defence24.pl/rss`) | 🇵🇱 Polska / Wschodnia Flanka NATO | Naruszenia przestrzeni powietrznej RP, komunikaty DO RSZ, MON, Straż Graniczna | `Aktywne` |
| [**@kpszsu**](https://t.me/kpszsu) | Telegram Web Stream | 🇺🇦 Ukraina | Raporty Dowództwa Sił Powietrznych UA, alarmy rakietowe, Shahedy | `Aktywne` |
| [**@war_monitor**](https://t.me/war_monitor) | Telegram Web Stream | 🇺🇦 Ukraina / 🇷🇺 Rosja | Radar wczesnego ostrzegania, trajektorie rakiet i bombowców strategicznych | `Aktywne` |
| [**@vanek_nikolaev**](https://t.me/vanek_nikolaev) | Telegram Web Stream | 🇺🇦 Ukraina | Radar operacyjny obrony przeciwlotniczej (OPL), meldunki bezpośrednie | `Aktywne` |
| [**@DeepStateUA**](https://t.me/DeepStateUA) | Telegram Web Stream | 🇺🇦 Ukraina | Dynamika i zmiany linii frontu, fortyfikacje, potwierdzenia terenowe | `Aktywne` |
| [**@astrapress**](https://t.me/astrapress) | Telegram Web Stream | 🇷🇺 Rosja | Niezależny OSINT – uderzenia w rafinerie (NPZ), bazy lotnicze i arsenały GRAU | `Aktywne` |
| [**@bazabazon**](https://t.me/bazabazon) | Telegram Web Stream | 🇷🇺 Rosja | Materiały wideo, pożary infrastruktury krytycznej i energetycznej w FR | `Aktywne` |
| [**@shot_shot**](https://t.me/shot_shot) | Telegram Web Stream | 🇷🇺 Rosja | Raporty z rosyjskich stref przygranicznych (Kursk, Biełgorod, Briańsk) | `Aktywne` |
| [**@rybar**](https://t.me/rybar) | Telegram Web Stream | 🇷🇺 Rosja / 🇺🇦 Ukraina | Wojskowy kanał analityczny, weryfikacja krzyżowa (cross-check) danych | `Aktywne` |
| [**@clashreport**](https://t.me/clashreport) | Telegram Web Stream | 🌐 Globalnie / Bliski Wschód | Starcia zbrojne: Izrael, Liban, Gaza, Morze Czerwone (Huti), Jemen, Sudan | `Aktywne` |
| [**@liveuamap**](https://t.me/liveuamap) | Telegram Web Stream | 🌐 Globalnie | Oficjalny globalny strumień zdarzeń i incydentów Liveuamap | `Aktywne` |
| [**Reddit r/CombatFootage**](https://www.reddit.com/r/CombatFootage/) | Telegram Bridge / Web | 🌐 Globalnie / Front UA | Weryfikowalne wideo z walk naziemnych, dronów FPV, uderzeń morskich | `Aktywne` |
| [**NASA FIRMS (VIIRS 375m)**](https://firms.modaps.eosdis.nasa.gov/) | REST API (Satelity) | 🛰️ Globalnie / Strefy Walk | Detekcja anomalii termicznych i pożarów po uderzeniach (FRP ≥ 25 MW) | `Aktywne (klucz opcjonalny)` |
| [**Google Translate / MyMemory**](https://translate.google.com/) | REST API | 🔄 Pomocnicze | Automatyczne tłumaczenie depesz obcojęzycznych na język polski | `Aktywne` |

---

## 🚀 Wdrożenie Online (GitHub Pages + Actions)

Projekt jest w pełni skonfigurowany pod darmowy hosting GitHub Pages i automatyzację GitHub Actions na koncie użytkownika.

- **Adres pulpitu online**: `https://simonkoszu.github.io/liveuamap-osint-monitor/`
- **Dostęp**: Wprowadź kod PIN `7749`.
- **Harmonogram**: GitHub Actions automatycznie pobiera nowe dane i aktualizuje raport 2 razy na dobę (06:00 i 18:00 UTC) oraz przy każdym `git push`.
