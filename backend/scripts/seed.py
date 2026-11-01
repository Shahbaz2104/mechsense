"""Seed the database with reproducible demo data.

Usage (from backend/):
    uv run python -m scripts.seed
    uv run python -m scripts.seed --force   # clear generated data first

Re-running without --force is safe: machines that already have readings are
skipped, so the dataset is never duplicated.
"""

import argparse
import logging

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.services.seeding import seed_demo_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed MechSense demo data")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Clear generated readings/events/work orders and rebuild them",
    )
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    with SessionLocal() as db:
        result = seed_demo_data(db, force=args.force)

    print("Seed complete:")
    print(f"  machines created : {result.machines_created}")
    print(f"  machines reused  : {result.machines_reused}")
    print(f"  readings created : {result.readings_created}")
    print(f"  work orders      : {result.work_orders_created}")
    if result.machines_skipped:
        print(f"  skipped (already seeded): {', '.join(result.machines_skipped)}")


if __name__ == "__main__":
    main()
