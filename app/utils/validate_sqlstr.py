import re
from fastapi import HTTPException
import sqlparse


def validate_sql(sql: str, max_limit: int = 10000) -> str:
    """Validate and sanitize a SQL query string."""
    parsed = sqlparse.parse(sql)
    if not parsed:
        raise HTTPException(status_code=400, detail="Invalid SQL")

    stmt = parsed[0]
    # Check SELECT
    if stmt.get_type().upper() != "SELECT":
        raise HTTPException(status_code=403, detail="Only SELECT queries allowed")

    # Check forbidden keywords
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "GRANT"]
    for token in stmt.flatten():
        if token.value.upper() in forbidden:
            raise HTTPException(
                status_code=403, detail=f"Forbidden keyword: {token.value}"
            )

    # Remove user-defined LIMIT and enforce our own
    sql_no_limit = re.sub(r"\s+LIMIT\s+\d+", "", sql, flags=re.IGNORECASE)

    # Finally, append our LIMIT
    sql = f"{sql_no_limit.strip().rstrip(';')} LIMIT {max_limit};"

    return sql
