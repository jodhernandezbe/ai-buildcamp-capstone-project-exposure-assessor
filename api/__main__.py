"""Command line: ``uv run python -m api`` serves the web interface on loopback."""

from __future__ import annotations

from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from uvicorn.config import LOGGING_CONFIG

from api.core.config import ui_settings
from api.core.logging_filter import uvicorn_log_config
from api.main import create_app

BUILD_HINT = (
    "The frontend is not built. Run: npm --prefix frontend ci && npm --prefix frontend run build"
)


def require_built_frontend(dist: Path) -> None:
    """Exit with the build command when ``dist`` has no built frontend."""
    if not (dist / "index.html").is_file():
        raise SystemExit(BUILD_HINT)


def main() -> None:
    """Serve the API and the built frontend on the configured loopback address.

    Loads ``.env`` first, like the command line program, so the tools find their service
    keys (Census, CompTox). The OpenAI key is not read from there: it comes from the keychain.
    """
    load_dotenv()
    settings = ui_settings()
    require_built_frontend(settings.frontend_dist)
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        log_config=uvicorn_log_config(LOGGING_CONFIG),
    )


if __name__ == "__main__":
    main()
