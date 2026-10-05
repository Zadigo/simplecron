from typing import Any

import pydantic
from pydantic import Field


class Context(pydantic.BaseModel):
    scheduler_uuid: str | None = Field(default=None)
    json_data: dict[str, Any] = Field(default_factory=dict)

    # class Context:
    #     def __init__(
    #         self, scheduler_uuid: str | None = None, json_data: dict[str, Any] | None = None
    #     ):
    #         self.scheduler_uuid = scheduler_uuid
    #         self.json_data = json_data or {}

    def _check_json_data(self):
        if self.json_data is None:
            self.json_data = {}

    def _check_increment(self, key: str):
        self._check_json_data()
        if key not in self.json_data or not isinstance(self.json_data[key], int):
            self.json_data[key] = 0

    def model_dump(self, **kwargs):
        values = {}
        for key, value in self.json_data.items():
            if not isinstance(value, (str, int, float, bool, type(None), list, dict)):
                value = str(value)
            values[key] = value

        values["scheduler_uuid"] = self.scheduler_uuid
        return values

    def reset_value(self, key: str):
        if key in self.json_data:
            self.json_data[key] = None
        return self

    def reset_all(self):
        for key in self.json_data:
            self.json_data[key] = None
        return self

    def toggle_value(self, key: str):
        self._check_json_data()

        if key not in self.json_data or not isinstance(self.json_data[key], bool):
            self.json_data[key] = False

        self.json_data[key] = not self.json_data[key]
        return self

    def increment_value(self, key: str, amount: int = 1) -> int:
        self._check_increment(key)
        self.json_data[key] += amount
        return self.json_data[key]

    def decrement_value(self, key: str, amount: int = 1) -> int:
        self._check_increment(key)
        self.json_data[key] -= amount
        print(self.json_data)
        return self.json_data[key]

    def set_value(self, key: str, value: Any):
        self._check_json_data()
        self.json_data[key] = value
        return self

    def get_value(self, key: str) -> Any:
        return self.json_data.get(key)
