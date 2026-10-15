"""Project-wide utilities with no knowledge of the rest of the project."""

from __future__ import annotations

from commons.units import UnitConversionError, convert

__all__ = ["UnitConversionError", "convert"]
