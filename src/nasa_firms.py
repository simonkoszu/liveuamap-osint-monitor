import os
import csv
import io
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

def get_firms_map_key():
    """Pobiera MAP_KEY ze zmiennych środowiskowych lub pliku .env"""
    # 1. Zmienna środowiskowa
    key = os.getenv("FIRMS_MAP_KEY") or os.getenv("MAP_KEY")
    if key and key.strip():
        return key.strip()

    # 2. Plik .env w katalogu projektu lub nadrzędnym
    for env_path in [
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
    ]:
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("#") or not line or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k in ("FIRMS_MAP_KEY", "MAP_KEY") and v:
                            return v
            except Exception:
                pass
    return None

def fetch_nasa_firms_hotspots(map_key=None, days=1):
    """
    Pobiera dane o pożarach i anomaliach termicznych z satelitów NASA VIIRS (375m)
    przez oficjalne REST API NASA FIRMS dla kluczowych teatrów operacyjnych.
    """
    key = map_key or get_firms_map_key()
    if not key:
        print("ℹ️ [NASA FIRMS] Brak klucza MAP_KEY w środowisku / pliku .env (opcjonalny).")
        print("   Warstwa satelitarna NASA WMS działa bezkluczykowo w interfejsie mapy.")
        return []

    print(f"🛰️ [NASA FIRMS] Wykryto aktywny klucz MAP_KEY (długość: {len(key)}). Pobieranie telemetrii satelitarnej...")

    # Kody państw ISO3 dla głównych stref operacyjnych
    TARGET_COUNTRIES = {
        "UKR": "Ukraina",
        "RUS": "Rosja",
        "ISR": "Izrael",
        "LBN": "Liban",
        "SYR": "Syria",
        "YEM": "Jemen"
    }

    satellite_events = []
    # Używamy sensora VIIRS SNPP NRT (Near Real-Time 375m)
    sensor = "VIIRS_SNPP_NRT"

    for iso3, country_name in TARGET_COUNTRIES.items():
        url = f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{key}/{sensor}/{iso3}/{days}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "AegisTacticalOSINT/2.4 (NASA FIRMS Hotspot Ingestion)"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    csv_text = resp.read().decode("utf-8", errors="replace")
                    if "latitude" not in csv_text or "Invalid MAP_KEY" in csv_text:
                        if "Invalid MAP_KEY" in csv_text:
                            print(f"⚠️ [NASA FIRMS] Niepoprawny MAP_KEY. Sprawdź poprawność klucza z wiadomości e-mail NASA.")
                            return []
                        continue

                    reader = csv.DictReader(io.StringIO(csv_text))
                    hotspots = list(reader)

                    # Filtrujemy tylko anomalie o wysokiej pewności (high confidence / FRP >= 20 MW)
                    significant_hotspots = []
                    for row in hotspots:
                        confidence = row.get("confidence", "nominal")
                        try:
                            frp = float(row.get("frp", 0.0) or 0.0)
                        except (ValueError, TypeError):
                            frp = 0.0
                        if confidence in ("h", "high") or frp >= 20.0:
                            significant_hotspots.append((row, frp))

                    if significant_hotspots:
                        print(f"   • {country_name} ({iso3}): wykryto {len(significant_hotspots)} istotnych anomalii termicznych (z {len(hotspots)} odczytów).")

                        # Sortujemy wg mocy promieniowania FRP i wybieramy najsilniejsze ogniska
                        significant_hotspots.sort(key=lambda x: x[1], reverse=True)
                        for spot, frp in significant_hotspots[:5]:
                            lat = float(spot["latitude"])
                            lon = float(spot["longitude"])
                            acq_date = spot.get("acq_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
                            acq_time = str(spot.get("acq_time", "1200")).zfill(4)
                            hour, minute = acq_time[:2], acq_time[2:]

                            ev_id = f"nasa_firms_{iso3}_{lat:.3f}_{lon:.3f}_{acq_date}"
                            ev = {
                                "id": ev_id,
                                "title": f"NASA Satellites detect intense thermal anomaly (FRP {frp:.1f} MW) near coordinates {lat:.3f}, {lon:.3f}",
                                "title_pl": f"Satelita NASA VIIRS wykrył intensywną anomalię termiczną / pożar (FRP: {frp:.1f} MW) w rejonie {country_name} [{lat:.3f}, {lon:.3f}]",
                                "text": f"NASA FIRMS VIIRS sensor detected an active thermal signature with {frp:.1f} MW radiative power on {acq_date} at {hour}:{minute} UTC. Likely impact, explosion, or industrial facility blaze.",
                                "text_pl": f"Czujnik NASA FIRMS VIIRS 375m zarejestrował anomalię termiczną o mocy {frp:.1f} MW w dniu {acq_date} o {hour}:{minute} UTC. Prawdopodobne miejsce uderzenia, eksplozji lub pożaru instalacji przemysłowej.",
                                "date": f"{acq_date} {hour}:{minute}:00",
                                "lat": lat,
                                "lng": lon,
                                "url": f"https://firms.modaps.eosdis.nasa.gov/map/#d:{acq_date}..{acq_date};l:viirs_snpp_nrt;@{lon:.2f},{lat:.2f},11z",
                                "category": "Eksplozja / Detonacja",
                                "threat_score": 0.90,
                                "source": "NASA FIRMS Satellite VIIRS"
                            }
                            satellite_events.append(ev)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print(f"⚠️ [NASA FIRMS] Błąd autoryzacji (HTTP 403). Upewnij się, że MAP_KEY został aktywowany.")
                break
            else:
                print(f"⚠️ [NASA FIRMS] HTTP {e.code} dla {iso3}: {e}")
        except Exception as e:
            print(f"⚠️ [NASA FIRMS] Błąd połączenia z API dla {iso3}: {e}")

    print(f"🛰️ [NASA FIRMS] Łącznie zarejestrowano {len(satellite_events)} taktycznych anomalii termicznych z orbity.")
    return satellite_events
