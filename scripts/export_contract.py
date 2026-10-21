"""Write the API contract JSON Schema to ``frontend/src/types/schema.json``.

Usage: ``uv run python -m scripts.export_contract``, after changing ``api/schemas/``; then
``npm --prefix frontend run gen:types``.
"""

from __future__ import annotations

from pathlib import Path

from api.schemas.contract import contract_json

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "frontend" / "src" / "types" / "schema.json"


def main() -> None:
    """Export the contract schema."""
    SCHEMA_PATH.write_text(contract_json(), encoding="utf-8")
    print(f"wrote {SCHEMA_PATH}")


if __name__ == "__main__":
    main()
