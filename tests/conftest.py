"""Shared pytest fixtures."""


def anyio_backend() -> str:
    """Force AnyIO tests to run on asyncio."""
    return "asyncio"
