from typing import Any

import pydantic
from pydantic import Field


class Context(pydantic.BaseModel):
    scheduler_uuid: str | None = Field(default=None)
    json_data: dict[str, Any] | None = Field(default_factory=dict)

    def _check_json_data(self):
        if self.json_data is None:
            self.json_data = {}

    def model_dump(self, **kwargs):
        for key, value in self.json_data.items():
            if not isinstance(value, (str, int, float, bool, type(None), list, dict)):
                self.json_data[key] = str(value)
        return super().model_dump(**kwargs)

    def reset_value(self, key: str):
        self._check_json_data()
        if key in self.json_data:
            self.json_data[key] = None
        return self

    def reset_all(self):
        self._check_json_data()
        for key in self.json_data:
            self.json_data[key] = None
        return self

    def toggle_value(self, key: str):
        self._check_json_data()

        if key not in self.json_data or not isinstance(self.json_data[key], bool):
            self.json_data[key] = False

        self.json_data[key] = not self.json_data[key]
        return self

    def increment_value(self, key: str, amount: int = 1):
        self._check_json_data()

        if key not in self.json_data or not isinstance(self.json_data[key], int):
            self.json_data[key] = 0

        self.json_data[key] += amount
        return self

    def decrement_value(self, key: str, amount: int = 1):
        self._check_json_data()

        if key not in self.json_data or not isinstance(self.json_data[key], int):
            self.json_data[key] = 0

        self.json_data[key] -= amount
        return self

    def set_value(self, key: str, value: Any):
        self._check_json_data()
        self.json_data[key] = value
        return self

    def get_value(self, key: str) -> Any:
        self._check_json_data()
        return self.json_data.get(key)
