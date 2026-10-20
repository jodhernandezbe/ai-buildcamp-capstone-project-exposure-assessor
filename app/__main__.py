"""Command line: ``uv run python -m app "Assess CAS 71-43-2"`` prints the agent's answer."""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from app.run import ask


def main() -> None:
    """Parse the question, run the agent with the configured model and print the answer."""
    parser = argparse.ArgumentParser(prog="python -m app", description=__doc__)
    parser.add_argument("question", help="what to assess, e.g. 'Assess CAS 71-43-2'")
    load_dotenv()
    print(ask(parser.parse_args().question))


if __name__ == "__main__":
    main()
