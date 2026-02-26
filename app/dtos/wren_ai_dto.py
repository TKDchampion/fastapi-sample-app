from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field


class AskRequestDTO(BaseModel):
    question: str = Field(..., description="Natural language question")
    threadId: Optional[str] = Field(None, description="Thread ID for the request")
    si_id: int = Field(..., description="SI ID for permission check")
    org_id: int = Field(..., description="Organization ID to look up chatbot credentials")


class GenerateSQLRequestDTO(BaseModel):
    question: str = Field(..., description="Natural language question")
    threadId: Optional[str] = Field(None, description="Thread ID for the request")
    si_id: int = Field(..., description="SI ID for permission check")
    org_id: int = Field(..., description="Organization ID to look up chatbot credentials")


class GenerateSQLResponseDTO(BaseModel):
    id: str
    sql: str
    threadId: str


class RunSQLRequestDTO(BaseModel):
    sql: str = Field(..., description="SQL query")
    threadId: Optional[str] = Field(None, description="Thread ID for the request")
    si_id: int = Field(..., description="SI ID for permission check")
    org_id: int = Field(..., description="Organization ID to look up chatbot credentials")


class ColumnDTO(BaseModel):
    name: str
    type: str


class RunSQLResponseDTO(BaseModel):
    id: str
    records: List[Any]
    columns: List[ColumnDTO]
    thread_id: Optional[str] = Field(..., alias="threadId")
    total_rows: Optional[int] = Field(..., alias="totalRows")


# Build the raw stream string once
FULL_SSE_VALUE = "\n".join(
    [
        'data: { "type": "message_start" }',
        "",
        "# SQL Generation Stages",
        'data: { "type": "state", "data": { "state": "sql_generation_start" }}',
        'data: { "type": "state", "data": { "state": "sql_generation_understanding" }}',
        'data: { "type": "state", "data": { "state": "sql_generation_searching" }}',
        'data: { "type": "state", "data": { "state": "sql_generation_planning" }}',
        'data: { "type": "state", "data": { "state": "sql_generation_generating" }}',
        'data: { "type": "state", "data": { "state": "sql_generation_success", "sql": "SELECT ... LIMIT 5", "dialectSql": "SELECT ... LIMIT 5" }}',
        "",
        "# SQL Execution",
        'data: { "type": "state", "data": { "state": "sql_execution_start" }}',
        'data: { "type": "state", "data": { "state": "sql_execution_end" }}',
        "",
        "# Summary Generation",
        'data: { "type": "content_block_start", "content_block": { "type": "text", "name": "summary_generation" }}',
        'data: { "type": "content_block_delta", "delta": { "text": "Here" }}',
        'data: { "type": "content_block_delta", "delta": { "text": " are" }}',
        'data: { "type": "content_block_delta", "delta": { "text": " the first 5 customers from the dataset." }}',
        'data: { "type": "content_block_stop" }',
        "",
        "# Stream ends",
        'data: { "type": "message_stop" }',
        "",
    ]
)

AskResponse = {
    "full_stream": {"summary": "An example full SSE stream", "value": FULL_SSE_VALUE}
}


class DataModel(BaseModel):
    values: List[Any] = Field(..., description="List of values for the Vega spec")


class VegaSpecModel(BaseModel):
    data: DataModel = Field(..., description="Data section of the Vega spec")

    class Config:
        extra = "allow"
        validate_by_name = True


class ChartResponseDTO(BaseModel):
    id: str = Field(..., description="Unique identifier")
    vegaSpec: VegaSpecModel = Field(..., alias="vegaSpec")
    threadId: str = Field(..., description="Thread identifier")


class ChartRequestDTO(BaseModel):
    question: str = Field(..., description="question")
    customInstruction: Literal["bar", "pie", "line"] = Field(
        ...,
        description="Chart type: 'bar' (柱狀圖), 'pie' (圓餅圖), 'line' (折線圖)",
    )
    sql: str = Field(..., description="SQL query")
    threadId: Optional[str] = Field(None, description="Thread ID for the request")
    si_id: int = Field(..., description="SI ID for permission check")
    org_id: int = Field(..., description="Organization ID to look up chatbot credentials")


class QueryTablesRequestDTO(BaseModel):
    query: str = Field(..., description="SQL string to query tables")


class QueryTableMessageResponseDTO(BaseModel):
    message: str
    total_rows: int
