from datetime import datetime, date
from pydantic import field_serializer


class DateOnlySerializerMixin:
    date_only_fields = ("contract_start", "contract_end")

    @field_serializer("*", when_used="json")
    def serialize_date_fields(self, value, field):
        if field.field_name in self.date_only_fields:
            if isinstance(value, datetime):
                return value.date().isoformat()
            if isinstance(value, date):
                return value.isoformat()
        return value
