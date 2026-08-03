"""Add the email-verification columns/table and backfill existing accounts.

`create_all` creates NEW tables but never alters existing ones, so the columns added to
`users` need an explicit ALTER. Existing accounts predate verification and would be
locked out by the new gate, so they are marked verified — they were created under the
old rules, and retroactively invalidating them would be a data-loss-shaped surprise.

Idempotent: safe to run more than once.

    python scripts/migrate_add_verification.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text  # noqa: E402

from app.database.base import Base  # noqa: E402
from app.database.session import engine  # noqa: E402
from app.models import *  # noqa: E402,F401,F403


def main() -> None:
    inspector = inspect(engine)

    if "users" not in inspector.get_table_names():
        print("No `users` table yet — run scripts/init_db.py first.")
        return

    existing = {column["name"] for column in inspector.get_columns("users")}
    is_sqlite = engine.dialect.name == "sqlite"
    bool_type = "BOOLEAN" if is_sqlite else "BOOLEAN"
    ts_type = "TIMESTAMP" if is_sqlite else "TIMESTAMP WITH TIME ZONE"

    with engine.begin() as connection:
        if "is_verified" not in existing:
            connection.execute(
                text(f"ALTER TABLE users ADD COLUMN is_verified {bool_type} NOT NULL DEFAULT FALSE")
            )
            print("+ users.is_verified")
        else:
            print("= users.is_verified already present")

        if "verified_at" not in existing:
            connection.execute(text(f"ALTER TABLE users ADD COLUMN verified_at {ts_type}"))
            print("+ users.verified_at")
        else:
            print("= users.verified_at already present")

    # Creates email_verifications (and anything else missing) without touching
    # tables that already exist.
    Base.metadata.create_all(bind=engine)
    print("= email_verifications ensured")

    with engine.begin() as connection:
        result = connection.execute(
            text(
                "UPDATE users SET is_verified = TRUE, verified_at = COALESCE(verified_at, created_at) "
                "WHERE is_verified = FALSE AND created_at < CURRENT_TIMESTAMP"
            )
        )
        print(f"= backfilled {result.rowcount} pre-existing account(s) as verified")

    print("\nDone. New sign-ups now require an emailed code.")


if __name__ == "__main__":
    main()
