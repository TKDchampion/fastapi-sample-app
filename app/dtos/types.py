from typing import Annotated
from datetime import datetime
from pydantic import Field

DateLikeDatetime = Annotated[
    datetime, Field(json_schema_extra={"format": "date"})  # Swagger 顯示成 date
]
