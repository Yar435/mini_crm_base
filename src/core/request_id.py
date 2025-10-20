# лёгкая обёртка вокруг contextvars
from contextvars import ContextVar
from typing import Optional

_request_id_ctx: ContextVar[Optional[str]] = ContextVar("_request_id_ctx", default=None)


def set_request_id(value: Optional[str]) -> None:
    _request_id_ctx.set(value)


def get_request_id() -> Optional[str]:
    return _request_id_ctx.get()
