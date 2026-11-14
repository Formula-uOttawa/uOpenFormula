import copy
from collections.abc import Callable
from typing import Any, Generic, TypeVar, overload

T = TypeVar("T")


class Saved(Generic[T]):
    """
    used for variables that should be saved when saving a project. (i.e. important state)

    Usage: `limits = Saved(lambda: [1, 2, 3])` on a StatefulView subclass.
    The lambda is the default value.
    """

    def __init__(self, default_factory: Callable[[], T]):
        self.default_factory = default_factory
        self.name = ""

    def __set_name__(self, owner, name: str):
        self.name = name
        # copy so subclasses don't mutate their parent's registry
        owner._saved_fields = {**getattr(owner, "_saved_fields", {}), name: self}

    def __get__(self, obj, owner=None):
        if obj is None:
            return self
        return obj._saved_values.setdefault(self.name, self.default_factory())

    def __set__(self, obj, value: T):
        obj._saved_values[self.name] = value


class StatefulView:
    _saved_fields: dict[str, Saved] = {}

    @property
    def _saved_values(self) -> dict[str, Any]:
        # lazily created so Saved attributes work even before attach_state()
        if "_saved_store" not in self.__dict__:
            self._saved_store: dict[str, Any] = {}
        return self._saved_store

    def attach_state(self, saved_state: dict | None = None):
        """Reset all Saved fields to defaults, then apply any matching saved values."""
        self._saved_store = {}
        for name, field in self._saved_fields.items():
            default = field.default_factory()
            value = (saved_state or {}).get(name, default)
            self._saved_store[name] = value if type(value) is type(default) else default
        self._state_initial = self.export_state()

    def reset_saved(self, name: str):
        """Reset one Saved field back to its default."""
        setattr(self, name, self._saved_fields[name].default_factory())

    def export_state(self) -> dict:
        return {name: copy.deepcopy(getattr(self, name)) for name in self._saved_fields}

    def is_state_diff(self) -> bool:
        return self.export_state() != self._state_initial

    def mark_state_saved(self):
        self._state_initial = self.export_state()
