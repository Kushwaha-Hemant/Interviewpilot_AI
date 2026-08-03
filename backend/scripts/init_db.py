"""Create every table from the SQLAlchemy metadata.

Fine for local development. For real deployments, generate Alembic migrations instead:
    alembic revision --autogenerate -m "message"
    alembic upgrade head
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.base import Base  # noqa: E402
from app.database.session import engine  # noqa: E402
from app.models import *  # noqa: E402,F401,F403  (registers every mapper)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    tables = ", ".join(sorted(Base.metadata.tables))
    print(f"Created/verified {len(Base.metadata.tables)} tables: {tables}")


if __name__ == "__main__":
    main()
