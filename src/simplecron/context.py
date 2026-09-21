from typing import Any

import pydantic
from pydantic import Field


class Context(pydantic.BaseModel):
    scheduler_uuid: str | None = Field(default=None)
    json_data: dict[str, Any] | None = Field(default=None)
