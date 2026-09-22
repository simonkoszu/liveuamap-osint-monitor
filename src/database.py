import json
import os
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class EventDatabase:
    """
    Bezpieczna baza danych zdarzeń Liveuamap w formacie JSON.
    Nie wymaga serwera bazodanowego, nie otwiera portów sieciowych,
    może być bezpośrednio wersjonowana w prywatnym repozytorium Git.
    """
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.events: Dict[str, Dict[str, Any]] = {}
        self.meta: Dict[str, Any] = {
            "tracking_started_at": datetime.now(timezone.utc).isoformat(),
            "last_updated_at": datetime.now(timezone.utc).isoformat(),
            "initial_event_count": 0
        }
        self.load()

    def _generate_event_id(self, timestamp: str, text: str) -> str:
        raw = f"{timestamp.strip()}_{text.strip()[:100]}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.meta = data.get("meta", self.meta)
                    self.events = data.get("events", {})
            except Exception as e:
                print(f"[DB] Ostrzeżenie: Błąd odczytu bazy {self.filepath}: {e}. Inicjalizacja nowej bazy.")
                self.events = {}

    def save(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.meta["last_updated_at"] = datetime.now(timezone.utc).isoformat()
        if "total_count" not in self.meta:
            self.meta["total_count"] = len(self.events)
        else:
            self.meta["total_count"] = len(self.events)

        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump({
                "meta": self.meta,
                "events": self.events
            }, f, ensure_ascii=False, indent=2)

    def add_event(self, event: Dict[str, Any]) -> bool:
        """
        Dodaje zdarzenie, jeśli jeszcze nie istnieje.
        Zwraca True jeśli dodano nowe, False jeśli duplikat.
        """
        event_id = event.get("id")
        if not event_id:
            event_id = self._generate_event_id(event.get("timestamp", ""), event.get("text", ""))
            event["id"] = event_id

        if event_id in self.events:
            return False

        # Ustaw datę dodania do bazy
        if "added_at" not in event:
            event["added_at"] = datetime.now(timezone.utc).isoformat()

        self.events[event_id] = event
        return True

    def get_all_events(self) -> List[Dict[str, Any]]:
        events = list(self.events.values())
        # Sortowanie od najnowszych do najstarszych
        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return events

    def get_events_between(self, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        result = []
        for ev in self.events.values():
            ts_str = ev.get("timestamp")
            if not ts_str:
                continue
            try:
                # Obsługa formatu ISO z timezone
                ev_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if start_dt <= ev_dt <= end_dt:
                    result.append(ev)
            except Exception:
                continue
        result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return result
