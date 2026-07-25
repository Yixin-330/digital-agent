from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class VenueDataService:
    def __init__(self) -> None:
        data_dir = Path(__file__).resolve().parent.parent / "data"
        self._venues: Dict[str, Dict[str, Any]] = {}
        self._load_directory(data_dir / "venues")
        if not self._venues:
            self._load_json(data_dir / "nuanquan_demo_data.json")

    def _load_directory(self, directory: Path) -> None:
        if not directory.exists():
            return
        for path in sorted(directory.glob("*.json")):
            self._load_json(path)

    def _load_json(self, path: Path) -> None:
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        venue_id = data.get("venue", {}).get("id")
        if venue_id:
            self._venues[venue_id] = data

    def infer_venue_id(self, venue_id: Optional[str], location: Optional[str], message: str = "") -> Optional[str]:
        if venue_id:
            return venue_id if venue_id in self._venues else None
        text = f"{location or ''} {message}".lower()
        for candidate_id, data in self._venues.items():
            if self._matches_venue(data, text):
                return candidate_id
        return None

    def get_venue(self, venue_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not venue_id:
            return None
        return self._venues.get(venue_id)

    def list_venues(self) -> List[Dict[str, Any]]:
        return [data["venue"] for data in self._venues.values()]

    def list_routes(self, venue_id: str) -> List[Dict[str, Any]]:
        venue = self.get_venue(venue_id)
        return list(venue.get("routes", [])) if venue else []

    def list_spots(self, venue_id: str) -> List[Dict[str, Any]]:
        venue = self.get_venue(venue_id)
        return list(venue.get("spots", [])) if venue else []

    def list_tasks(self, venue_id: str) -> List[Dict[str, Any]]:
        venue = self.get_venue(venue_id)
        return list(venue.get("tasks", [])) if venue else []

    def list_products(self, venue_id: str) -> List[Dict[str, Any]]:
        venue = self.get_venue(venue_id)
        return list(venue.get("products", [])) if venue else []

    def venue_name(self, venue_id: str) -> str:
        venue = self.get_venue(venue_id)
        if not venue:
            return venue_id
        return str(venue.get("venue", {}).get("name", venue_id))

    def _matches_venue(self, data: Dict[str, Any], text: str) -> bool:
        venue = data.get("venue", {})
        tokens: List[str] = [str(venue.get("id", "")), str(venue.get("name", ""))]
        tokens.extend(str(alias) for alias in venue.get("aliases", []))
        location = venue.get("location", {})
        if isinstance(location, dict):
            tokens.extend(str(value) for value in location.values())
        for spot in data.get("spots", []):
            tokens.append(str(spot.get("name", "")))
        for route in data.get("routes", []):
            tokens.append(str(route.get("name", "")))
        return any(token and token.lower() in text for token in tokens)
