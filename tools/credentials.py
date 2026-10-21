"""The API keys available to tools that call a provider or service themselves.

The web program provides the keys stored in the OS keychain for the duration of one turn
(``PROVIDER_KEY.provide(key)`` and so on); each tool reads its key with ``.get()`` at the moment
it needs it, never keeping it, and falls back to its configured environment variable when none
is provided (CLI, evaluations).
"""

from __future__ import annotations

from collections.abc import Mapping

from commons.scoped_secret import ScopedSecret

PROVIDER_KEY = ScopedSecret("provider_api_key")  # OpenAI embeddings (SCC lookup)
CENSUS_KEY = ScopedSecret("census_api_key")  # Census Data API (population receptors)
COMPTOX_KEY = ScopedSecret("comptox_api_key")  # CompTox Chemicals Dashboard API

# Each stored key (see ``config.ui.KEY_NAMES``) and the holder that gives it to its tools.
HOLDERS: Mapping[str, ScopedSecret] = {
    "openai": PROVIDER_KEY,
    "census": CENSUS_KEY,
    "comptox": COMPTOX_KEY,
}
