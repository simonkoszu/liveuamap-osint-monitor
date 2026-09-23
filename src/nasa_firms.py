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
    przez oficjalne REST API NASA FIRMS (endpoint area/csv) dla kluczowych teatrów operacyjnych.
    """
    key = map_key or get_firms_map_key()
    if not key:
        print("ℹ️ [NASA FIRMS] Brak klucza MAP_KEY w środowisku / pliku .env (opcjonalny).")
        print("   Warstwa satelitarna NASA WMS działa bezkluczykowo w interfejsie mapy.")
        return []

    print(f"🛰️ [NASA FIRMS] Wykryto aktywny klucz MAP_KEY (długość: {len(key)}). Pobieranie telemetrii satelitarnej...")

    # Bounding Boxy (west, south, east, north) dla teatrów działań wojennych
    TARGET_AREAS = [
        ("Ukraina / Donbas / Krym", "22.0,44.0,40.5,52.5"),
        ("Izrael / Liban / Syria", "33.5,30.0,38.5,35.5"),
        ("Morze Czerwone & Jemen", "41.0,12.5,53.5,18.5"),
        ("Irak & Zatoka Perska", "43.5,30.0,49.5,36.5"),
    ]

    satellite_events = []
    sensor = "VIIRS_SNPP_NRT" # Suomi-NPP VIIRS 375m NRT

    for area_name, bbox in TARGET_AREAS:
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{sensor}/{bbox}/{days}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "AegisTacticalOSINT/2.4 (NASA FIRMS Hotspot Ingestion)"}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                if resp.status == 200:
                    csv_text = resp.read().decode("utf-8", errors="replace")
                    if "latitude" not in csv_text or "Invalid MAP_KEY" in csv_text:
                        if "Invalid MAP_KEY" in csv_text:
                            print(f"⚠️ [NASA FIRMS] Błąd autoryzacji: NASA zgłasza 'Invalid MAP_KEY'. Sprawdź klucz.")
                            return []
                        continue

                    reader = csv.DictReader(io.StringIO(csv_text))
                    hotspots = list(reader)

                    # Filtrujemy tylko silne anomalie o wysokiej pewności (FRP >= 25.0 MW lub high confidence)
                    significant_hotspots = []
                    for row in hotspots:
                        conf = str(row.get("confidence", "nominal")).lower()
                        try:
                            frp = float(row.get("frp", 0.0) or 0.0)
                        except (ValueError, TypeError):
                            frp = 0.0

                        if conf in ("h", "high") or frp >= 25.0:
                            significant_hotspots.append((row, frp))

                    if significant_hotspots:
                        print(f"   • {area_name}: wykryto {len(significant_hotspots)} istotnych anomalii termicznych (z {len(hotspots)} odczytów).")

                        # Wybieramy top 6 najsilniejszych anomalii
                        significant_hotspots.sort(key=lambda x: x[1], reverse=True)
                        for spot, frp in significant_hotspots[:6]:
                            lat = float(spot["latitude"])
                            lon = float(spot["longitude"])
                            acq_date = spot.get("acq_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
                            acq_time = str(spot.get("acq_time", "1200")).zfill(4)
                            hour, minute = acq_time[:2], acq_time[2:]

                            ev_id = f"nasa_firms_{lat:.3f}_{lon:.3f}_{acq_date}_{acq_time}"
                            iso_ts = f"{acq_date}T{hour}:{minute}:00+00:00"
                            ev = {
                                "id": ev_id,
                                "title": f"NASA Satellites detect intense thermal anomaly (FRP {frp:.1f} MW) near {area_name}",
                                "title_pl": f"Satelita NASA VIIRS zarejestrował anomalię termiczną / eksplozję (FRP: {frp:.1f} MW) w rejonie {area_name} [{lat:.3f}, {lon:.3f}]",
                                "text": f"NASA FIRMS VIIRS sensor detected an active thermal signature with {frp:.1f} MW radiative power on {acq_date} at {hour}:{minute} UTC. Likely impact, explosion, or industrial facility blaze.",
                                "text_pl": f"Czujnik NASA FIRMS VIIRS 375m zarejestrował punktową anomalię termiczną o mocy {frp:.1f} MW w dniu {acq_date} o {hour}:{minute} UTC. Prawdopodobne miejsce uderzenia, eksplozji lub pożaru instalacji przemysłowej.",
                                "timestamp": iso_ts,
                                "date": f"{acq_date} {hour}:{minute}:00",
                                "lat": lat,
                                "lon": lon,
                                "lng": lon,
                                "country": "Czujniki NASA",
                                "flag": "🛰️",
                                "theater": f"Monitoring Satelitarny ({area_name})",
                                "location_name": f"{area_name} [{lat:.2f}, {lon:.2f}]",
                                "url": f"https://firms.modaps.eosdis.nasa.gov/map/#d:{acq_date}..{acq_date};l:viirs_snpp_nrt;@{lon:.2f},{lat:.2f},11z",
                                "event_type": "Anomalia Termiczna",
                                "tactical_category": "Czujnik NASA FIRMS",
                                "tactical_icon": "🛰️",
                                "threat_score": 0.90,
                                "source": "NASA FIRMS Satellite VIIRS",
                                "source_channel": "NASA FIRMS",
                                "is_fire": True,
                                "is_nasa": True,
                                "frp": frp
                            }
                            satellite_events.append(ev)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print(f"⚠️ [NASA FIRMS] HTTP 403: Odmowa dostępu. Klucz MAP_KEY nie ma jeszcze uprawnień.")
                break
            else:
                err_msg = e.read().decode("utf-8", errors="replace")
                print(f"⚠️ [NASA FIRMS] HTTP {e.code} dla {area_name}: {err_msg}")
        except Exception as e:
            print(f"⚠️ [NASA FIRMS] Błąd połączenia dla {area_name}: {e}")

    print(f"🛰️ [NASA FIRMS] Łącznie zarejestrowano {len(satellite_events)} taktycznych anomalii termicznych z orbity.")
    return satellite_events
