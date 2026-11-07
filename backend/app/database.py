from typing import Any

from fastapi import Request
from pymongo import DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database


def ensure_indexes(database: Database[dict[str, Any]]) -> None:
    database.medicoes.create_index(
        [("timestamp", DESCENDING), ("_id", DESCENDING)],
        name="medicoes_recentes",
    )


def get_collection(request: Request) -> Collection[dict[str, Any]]:
    """Tenta criar o índice novamente se o MongoDB não estava pronto no startup."""
    if not request.app.state.index_ready:
        ensure_indexes(request.app.state.database)
        request.app.state.index_ready = True
    return request.app.state.database.medicoes
