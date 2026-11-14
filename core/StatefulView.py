import copy


class StatefulView:
    STATE: dict = {}

    def attach_state(self, saved_state: dict | None = None):
        self._state = copy.deepcopy(self.STATE)
        for key, value in (saved_state or {}).items():
            if key in self._state and type(value) is type(self._state[key]):
                self._state[key] = value
        self._state_initial = copy.deepcopy(self._state)

    @property
    def state(self):
        return self._state

    def export_state(self) -> dict:
        return copy.deepcopy(self._state)

    def is_state_diff(self) -> bool:
        return self._state != self._state_initial

    def mark_state_saved(self):
        self._state_initial = copy.deepcopy(self._state)

    def set_state(self, key, value):
        if key not in self.STATE:
            raise KeyError(f"'{key}' not in state")
        self._state[key] = value
