"""Placeholder synthetic data generator.

Run from the ``backend`` directory so that ``app`` is importable:

    cd backend && python ../data/synthetic/generate.py
"""

from app.db import SessionLocal


def main() -> None:
    with SessionLocal() as session:  # noqa: F841 - seeding logic lands in a later PR
        print("No synthetic generators defined yet.")


if __name__ == "__main__":
    main()
