#!/usr/bin/env python
"""Django's command-line utility for administrative tasks.

CLI entry point for the Ledger de Certificados de Conformidad backend.
"""
import os
import sys


def main() -> None:
    """Run administrative tasks.

    :raises ImportError: if Django is not installed or the virtualenv is not active.
    :rtype: None
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover - environment guard
        raise ImportError(
            "Could not import Django. Is it installed and available on your "
            "PYTHONPATH? Did you forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
