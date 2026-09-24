# ⚡ Cloudflare Worker Relay dla Aegis OSINT Radar

Umożliwia uruchamianie świeżego skanu i generowanie raportu **1 kliknięciem z dowolnego urządzenia (telefon, tablet, komputer)** bez logowania się do GitHuba.

---

## 🚀 Instrukcja wdrożenia w 2 minuty (Darmowe konto Cloudflare)

### Krok 1: Załóż darmowe konto na Cloudflare (jeśli jeszcze nie masz)
Wejdź na: [dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up) (darmowy plan zawiera 100 000 zapytań dziennie).

### Krok 2: Utwórz nowego Workera
1. W lewym menu Cloudflare kliknij **Workers & Pages** → **Overview**.
2. Kliknij niebieski przycisk **Create application** → zakładka **Workers** → **Create Worker**.
3. Nadaj nazwę, np. `aegis-radar-relay`, i kliknij **Deploy**.

### Krok 3: Wklej kod
1. Kliknij **Edit code** w prawym górnym rogu.
2. Skasuj domyślny kod i wklej w całości zawartość pliku [`worker.js`](worker.js).
3. Kliknij **Save and deploy**.

### Krok 4: Dodaj Twój GitHub Token jako bezpieczną zmienną środowiskową
1. Wróć do ekranu swojego Workera i wejdź w zakładkę **Settings** → **Variables and Secrets**.
2. W sekcji *Environment Variables* kliknij **Add**.
3. Wpisz:
   * **Variable name:** `GH_TOKEN`
   * **Value:** Twój GitHub Personal Access Token (np. `ghp_...` z uprawnieniem `workflow` lub `repo`).
   * Kliknij **Encrypt** (opcjonalnie, żeby ukryć wartość) i kliknij **Save and deploy**.

---

## 🌐 Gotowy adres URL
Twój worker otrzyma unikalny publiczny adres, np.:
`https://aegis-radar-relay.<twoja-nazwa>.workers.dev`

Wklej ten adres w konfiguracji raportu lub w pliku konfiguracyjnym, a przycisk **„Odśwież”** będzie natychmiast wyzwalał skan w chmurze bez żadnego logowania!
