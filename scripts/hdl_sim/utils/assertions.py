"""Simple check helpers for cocotb tests."""


def assert_equals(actual, expected, msg: str | None = None) -> None:
    """Fail if ``actual == expected`` is false."""
    if msg is None:
        msg = f"expected {expected!r}, got {actual!r}"
    assert actual == expected, msg
