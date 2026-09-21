from typing import Any

import pydantic


class Context(pydantic.BaseModel):
    json_message: dict[str, Any] | None = None
