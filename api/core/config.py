"""The API's view of the ``[ui]`` settings (the single source is ``config/settings.toml``)."""

from __future__ import annotations

from config.ui import UiSettings, get_ui_settings


def ui_settings() -> UiSettings:
    """Return the cached UI settings; the one place the API reads them."""
    return get_ui_settings()
