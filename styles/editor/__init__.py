"""Editor style registry (selection metadata only)."""

from __future__ import annotations

from typing import Any

__all__ = [
    "EditorStyleError",
    "UnknownStyleError",
    "get_style",
    "list_styles",
    "normalize_query",
    "resolve_style",
]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from . import loader

        return getattr(loader, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
