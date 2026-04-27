"""Allow `python -m object_tracker` to invoke the CLI."""

from .cli import app

if __name__ == "__main__":
    app()
