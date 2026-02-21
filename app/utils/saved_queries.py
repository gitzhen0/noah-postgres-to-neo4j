"""
Persistent saved-query store backed by a local JSON file.
"""

import json
from datetime import datetime
from pathlib import Path

_STORE = Path(__file__).parent.parent / "saved_queries.json"


def _load() -> list[dict]:
    if not _STORE.exists():
        return []
    try:
        return json.loads(_STORE.read_text())
    except Exception:
        return []


def _save(queries: list[dict]) -> None:
    _STORE.write_text(json.dumps(queries, indent=2))


def list_saved() -> list[dict]:
    """Return all saved queries, newest first."""
    return list(reversed(_load()))


def save_query(name: str, cypher: str) -> None:
    """Append a new saved query (or overwrite if name already exists)."""
    queries = _load()
    # Remove existing entry with same name
    queries = [q for q in queries if q["name"] != name]
    queries.append({
        "name": name,
        "cypher": cypher,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    _save(queries)


def delete_query(name: str) -> None:
    queries = [q for q in _load() if q["name"] != name]
    _save(queries)
