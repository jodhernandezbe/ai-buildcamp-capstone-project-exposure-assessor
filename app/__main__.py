"""Command line: ``uv run python -m app "Assess CAS 71-43-2"`` prints the agent's answer.

The answer goes to stdout; the run's token usage and estimated cost go to stderr, so piping the
answer stays clean. When Logfire is set up the run is also recorded as a trace.
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from app.run import ask
from app.telemetry import configure_telemetry
from app.usage_meter import format_usage, summarize_calls
from config.telemetry import get_telemetry_settings
from config.ui import get_ui_settings


def main() -> None:
    """Parse the question, run the agent with the configured model, print the answer and the
    cost summary."""
    parser = argparse.ArgumentParser(prog="python -m app", description=__doc__)
    parser.add_argument("question", help="what to assess, e.g. 'Assess CAS 71-43-2'")
    load_dotenv()  # before monitoring, which reads the Logfire token from the environment
    configure_telemetry(get_telemetry_settings())
    result = ask(parser.parse_args().question)
    print(result.answer)
    total = summarize_calls(result.calls, get_ui_settings().pricing)
    print(format_usage(total), file=sys.stderr)


if __name__ == "__main__":
    main()
