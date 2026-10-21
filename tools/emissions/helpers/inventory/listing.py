"""What the model is told about an inventory: filtered, ranked and capped."""

from __future__ import annotations

from collections.abc import Sequence

from tools.schemas import EmissionRecord, InventoryResult


def _matches(record: EmissionRecord, state: str | None, city: str | None) -> bool:
    if state is not None and (record["state"] or "").strip().upper() != state:
        return False
    return city is None or (record["city"] or "").strip().upper() == city


def _clean(value: str | None) -> str | None:
    text = (value or "").strip().upper()
    return text or None


def _note(matching: int, shown: int, filtered: bool) -> str | None:
    if matching == 0:
        return "No facility matches the filters." if filtered else None
    if matching <= shown:
        return None
    return (
        f"Only the {shown} facilities with the highest emission rates of the {matching} that "
        "match are listed; the others are not shown and the list must not be treated as "
        "complete. Give `state` or `city` to see the largest in one place."
    )


def rank_and_cap(
    records: Sequence[EmissionRecord],
    max_listed: int,
    state: str | None = None,
    city: str | None = None,
) -> tuple[InventoryResult, list[EmissionRecord]]:
    """Rank facilities by emission rate and cap what the model sees.

    Args:
        records: Every facility found for the chemical.
        max_listed: Most facilities listed to the model.
        state: Keep only facilities in this state (postal abbreviation, any case).
        city: Keep only facilities in this city (any case, exact name).

    Returns:
        The model's view (``InventoryResult``) and the complete matching list, largest
        emission rate first, for the interface.
    """
    wanted_state, wanted_city = _clean(state), _clean(city)
    matching = sorted(
        (r for r in records if _matches(r, wanted_state, wanted_city)),
        key=lambda r: r["emission_rate"],
        reverse=True,
    )
    listed = matching[:max_listed]
    filtered = wanted_state is not None or wanted_city is not None
    result: InventoryResult = {
        "total_found": len(records),
        "matching": len(matching),
        "shown": len(listed),
        "facilities": listed,
        "note": _note(len(matching), len(listed), filtered),
    }
    return result, matching
