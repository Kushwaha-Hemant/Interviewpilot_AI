"""Portable column types.

Postgres is the target database and gets real JSONB (indexable, binary). Any other
dialect — SQLite for a quick local run or a fast test suite — falls back to plain JSON,
so the same models work everywhere without conditional code in each file.
"""

from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

JSONType = JSON().with_variant(JSONB, "postgresql")
