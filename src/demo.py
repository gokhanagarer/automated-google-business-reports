"""Entrypoint for `make demo` — runs end-to-end against the bundled fixture, no API keys."""

from .main import main

if __name__ == "__main__":
    raise SystemExit(main())
