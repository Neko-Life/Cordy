from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, TypeVar, Union
import inspect
from time import perf_counter

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

__all__ = (
    "Json",
    "Msg",
    "loads", "dumps",
    "make_proxy_for"
)

# Swappable json encoders and decoders to be used in the library
Json = Union[dict[str, Any], list[Union[dict[str, Any], Any]]]
Msg = dict[str, Any]

loads: Callable[[str], Any] = json.loads # Any allows custom type without cast
dumps: Callable[[Json], str] = lambda dat: json.dumps(dat, separators=(',', ':'))


if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Protocol

    class SlottedClass(Protocol):
        __slots__: Sequence[str]
        __mro__: tuple[type, ...]

    C = TypeVar("C", bound=SlottedClass)
    K = TypeVar("K")

def make_proxy_for(org_cls: C, /, *, attr: str, proxied_attrs: Iterable[str] = None, proxied_methods: Iterable[str] = None):
    def deco(cls: K) -> K:
        def make_encapsulators(name: str):
            nonlocal attr

            def fset(_, _1, _2):
                raise TypeError(f"Cannot mutate attribute '{name}' on a {cls} instance")

            def fdel(_, _1):
                raise TypeError(f"Cannot delete attribute '{name}' on a {cls} instance")

            return {
                "fget": lambda s: getattr(s, "name"),
                "fset": fset,
                "fdel": fdel
            }

        proxied = (
            it for it in (
                proxied_attrs or (
                    getattr(c, '__slots__', tuple()) for c in org_cls.__mro__
                ),
                proxied_methods or (
                    m[0] for m in inspect.getmembers(org_cls, predicate=inspect.isfunction) if not hasattr(cls, m[0])
                )
            ) if it is not None
        )

        for s in proxied:
            setattr(cls, s, property(**make_encapsulators(s)))

        return cls
    return deco

class Timer:
    """A context mangager to time code

    Attributes
    ==========
    time : :class:`int`, :data:`None`, ``int | None``
        The real time taken to exit the context manager.
        when context manager has not exited it stores the value of
        the performance counter used by :func:`time.perf_counter`
    """
    __slots__ = ("time",)

    delta: None | int

    def __init__(self) -> None:
        self.time = None

    def __enter__(self):
        self.time = perf_counter()
        return self

    def __exit__(self, *exc_info):
        self.time -= perf_counter()