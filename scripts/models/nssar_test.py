"""Plot a noise-shaping SAR conversion.

Run from the repository root with ``scripts`` on ``PYTHONPATH``::

    PYTHONPATH=scripts uv run python -m models.nssar_test
"""

from models.nssar import main


if __name__ == "__main__":
    main()
