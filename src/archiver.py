import os
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple, Optional
import urllib.request
import urllib.error

class HistoricalArchiver:
    """
    Moduł Długoterminowej Archiwizacji & Bazy Historycznej (ML Training Dataset):
    - Utrzymuje kroczące okno retencji (14 dni) w aktywnej bazie operacyjnej
    - Starsze incydenty przenosi bezpiecznie do bazy historycznej (data/archive/)
    - Generuje format JSONL (JSON Lines) zoptymalizowany pod Machine Learning / BigQuery / Pandas
    - Wspiera opcjonalną synchronizację w chmurze (Google Drive Webhook / Cloud Storage)
    """

    def __init__(self, base_dir: Optional[str] = None):
        if not base_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = base_dir
        self.archive_dir = os.path.join(self.base_dir, "data", "archive")
        os.makedirs(self.archive_dir, exist_ok=True)

        self.archive_json_path = os.path.join(self.archive_dir, "events_archive.json")
        self.archive_jsonl_path = os.path.join(self.archive_dir, "historical_dataset.jsonl")
        self.manifest_path = os.path.join(self.archive_dir, "archive_manifest.json")

        self.archived_events: Dict[str, Dict[str, Any]] = {}
        self.manifest: Dict[str, Any] = {
            "total_archived": 0,
            "retention_days": 14,
            "first_archived_at": None,
            "last_archived_at": None,
            "oldest_event_timestamp": None,
            "newest_event_timestamp": None,
            "cloud_sync_enabled": bool(os.environ.get("GDRIVE_WEBHOOK_URL"))
        }
        self._load_existing_archive()

    def _load_existing_archive(self):
        """Ładuje istniejące archiwum, aby uniknąć duplikacji rekordów."""
        if os.path.exists(self.archive_json_path):
            try:
                with open(self.archive_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.archived_events = data.get("events", {})
                    self.manifest = data.get("manifest", self.manifest)
            except Exception as e:
                print(f"[ARCHIVER] Ostrzeżenie: Błąd odczytu {self.archive_json_path}: {e}")
                self.archived_events = {}

    def process_retention(
        self,
        events: List[Dict[str, Any]],
        retention_days: int = 14
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Dzieli zbiór zdarzeń na:
        - Aktywne (ostatnie retention_days, domyślnie 14)
        - Archiwalne (starsze niż retention_days)

        Zwraca: (active_events, newly_archived_events, archive_stats)
        """
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=retention_days)

        active_events = []
        to_archive = []

        for ev in events:
            ts_str = ev.get("timestamp")
            is_old = False
            if ts_str:
                try:
                    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if dt < cutoff_date:
                        is_old = True
                except Exception:
                    # Jeśli nie da się sparsować timestampu, sprawdzamy added_at
                    added_str = ev.get("added_at")
                    if added_str:
                        try:
                            adt = datetime.fromisoformat(added_str.replace("Z", "+00:00"))
                            if adt < cutoff_date:
                                is_old = True
                        except Exception:
                            pass
            else:
                is_old = True

            if is_old:
                to_archive.append(ev)
            else:
                active_events.append(ev)

        newly_archived = []
        for ev in to_archive:
            eid = ev.get("id")
            if not eid:
                continue
            if eid not in self.archived_events:
                # Oznacz datę archiwizacji
                ev_copy = dict(ev)
                ev_copy["archived_at"] = now.isoformat()
                self.archived_events[eid] = ev_copy
                newly_archived.append(ev_copy)

        if newly_archived:
            self._save_archive(newly_archived)
            self._sync_to_cloud(newly_archived)

        stats = {
            "retention_days": retention_days,
            "active_count": len(active_events),
            "newly_archived_count": len(newly_archived),
            "total_archived": len(self.archived_events),
            "archive_dir": self.archive_dir,
            "jsonl_file": self.archive_jsonl_path,
            "json_file": self.archive_json_path,
            "cloud_sync_enabled": bool(os.environ.get("GDRIVE_WEBHOOK_URL"))
        }

        return active_events, newly_archived, stats

    def _save_archive(self, newly_archived: List[Dict[str, Any]]):
        """Zapisuje archiwum w formatach JSON oraz JSONL."""
        now_iso = datetime.now(timezone.utc).isoformat()
        self.manifest["total_archived"] = len(self.archived_events)
        self.manifest["last_archived_at"] = now_iso
        if not self.manifest.get("first_archived_at"):
            self.manifest["first_archived_at"] = now_iso

        # Aktualizacja min/max timestampów
        all_timestamps = [e.get("timestamp") for e in self.archived_events.values() if e.get("timestamp")]
        if all_timestamps:
            self.manifest["oldest_event_timestamp"] = min(all_timestamps)
            self.manifest["newest_event_timestamp"] = max(all_timestamps)

        # 1. Zapis pliku JSON
        with open(self.archive_json_path, "w", encoding="utf-8") as f:
            json.dump({
                "manifest": self.manifest,
                "events": self.archived_events
            }, f, ensure_ascii=False, indent=2)

        # 2. Dopisanie do pliku JSONL (Format treningowy pod Machine Learning)
        with open(self.archive_jsonl_path, "a", encoding="utf-8") as f:
            for ev in newly_archived:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")

        # 3. Zapis manifestu
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)

        print(f"[ARCHIVER] Zarchiwizowano {len(newly_archived)} zdarzeń. Łącznie w bazie historycznej: {len(self.archived_events)}.")

    def _sync_to_cloud(self, newly_archived: List[Dict[str, Any]]):
        """
        Opcjonalny eksport do Google Drive / Cloud Webhook.
        Jeśli skonfigurowano GDRIVE_WEBHOOK_URL w zmiennych środowiskowych lub GitHub Secrets,
        wysyła paczkę zdarzeń przez HTTP POST do Google Apps Script zapisującego pliki na Dysku Google.
        """
        webhook_url = os.environ.get("GDRIVE_WEBHOOK_URL")
        if not webhook_url:
            return

        try:
            payload = {
                "source": "Aegis OSINT Radar",
                "synced_at": datetime.now(timezone.utc).isoformat(),
                "batch_count": len(newly_archived),
                "total_archived": len(self.archived_events),
                "events": newly_archived
            }
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if 200 <= resp.status < 300:
                    print(f"☁️ [GOOGLE DRIVE] Pomyślnie zsynchronizowano {len(newly_archived)} zdarzeń z Dyskiem Google.")
                else:
                    print(f"⚠️ [GOOGLE DRIVE] Serwer chmury zwrócił kod: {resp.status}")
        except Exception as e:
            print(f"ℹ️ [GOOGLE DRIVE] Eksport do chmury nie powiódł się: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki bazy archiwalnej do raportu."""
        return {
            "total_archived": len(self.archived_events),
            "retention_days": self.manifest.get("retention_days", 14),
            "oldest_timestamp": self.manifest.get("oldest_event_timestamp"),
            "last_archived_at": self.manifest.get("last_archived_at"),
            "cloud_sync_enabled": bool(os.environ.get("GDRIVE_WEBHOOK_URL"))
        }
