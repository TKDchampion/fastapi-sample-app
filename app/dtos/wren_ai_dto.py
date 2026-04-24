from datetime import datetime
from enum import Enum
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class CreateMessageDTO(BaseModel):
    role: Literal["user", "system", "assistant", "tool"] = Field(
        "user", description="Message role"
    )
    content_type: Literal[
        "text", "markdown", "json", "tool_call", "tool_result", "image_ref", "error"
    ] = Field("text", description="Content type")
    content_text: Optional[str] = Field(None, description="Text content")
    content_json: Optional[dict] = Field(None, description="JSON content")
    status: Literal["final", "streaming", "failed", "cancelled"] = Field(
        "final", description="Message status"
    )
    parent_message_id: Optional[str] = Field(
        None, description="Parent message ID (UUID)"
    )


class AskRequestDTO(BaseModel):
    question: str = Field(..., description="Natural language question")
    wren_ai_thread_id: Optional[str] = Field(
        None, description="Wren thread ID for the request"
    )
    thread_id: Optional[str] = Field(
        None, description="System thread ID (returned after first ask)"
    )
    title: Optional[str] = Field(
        None, description="Thread title, required when creating a new conversation"
    )
    si_id: int = Field(..., description="SI ID for permission check")
    org_id: int = Field(
        ..., description="Organization ID to look up chatbot credentials"
    )

    @model_validator(mode="after")
    def validate_thread_and_title(self):
        has_wren = self.wren_ai_thread_id is not None
        has_thread = self.thread_id is not None

        if not has_wren and not has_thread:
            # 新增情境：title 必填
            if not self.title:
                raise ValueError(
                    "title is required when creating a new conversation (wren_ai_thread_id and thread_id are both absent)"
                )
        else:
            # 繼續情境：wren_ai_thread_id 和 thread_id 必須同時填
            if not has_wren or not has_thread:
                raise ValueError(
                    "wren_ai_thread_id and thread_id must both be provided together"
                )

        return self


class GenerateSQLRequestDTO(BaseModel):
    question: str = Field(..., description="Natural language question")
    wren_ai_thread_id: Optional[str] = Field(
        None, description="Wren AI thread ID for the request"
    )
    si_id: int = Field(..., description="SI ID for permission check")
    org_id: int = Field(
        ..., description="Organization ID to look up chatbot credentials"
    )


class GenerateSQLResponseDTO(BaseModel):
    id: str
    sql: str
    wren_ai_thread_id: str = Field(..., alias="threadId")

    class Config:
        populate_by_name = True


class RunSQLRequestDTO(BaseModel):
    sql: str = Field(..., description="SQL query")
    wren_ai_thread_id: Optional[str] = Field(
        None, description="Wren AI thread ID for the request"
    )
    si_id: int = Field(..., description="SI ID for permission check")
    org_id: int = Field(
        ..., description="Organization ID to look up chatbot credentials"
    )
    thread_id: Optional[str] = Field(
        None, description="System thread UUID for artifact creation"
    )
    message_id: Optional[str] = Field(
        None, description="Message UUID to attach artifact to"
    )
    title: Optional[str] = Field(
        None, description="Artifact title, required when message_id is provided"
    )


class ColumnDTO(BaseModel):
    name: str
    type: str


class RunSQLResponseDTO(BaseModel):
    id: str
    records: List[Any]
    columns: List[ColumnDTO]
    wren_ai_thread_id: Optional[str] = Field(..., alias="threadId")
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
    wren_ai_thread_id: str = Field(
        ..., alias="threadId", description="Wren AI thread identifier"
    )

    class Config:
        populate_by_name = True


class ChartRequestDTO(BaseModel):
    question: str = Field(..., description="question")
    customInstruction: Literal["bar", "pie", "line"] = Field(
        ...,
        description="Chart type: 'bar' (柱狀圖), 'pie' (圓餅圓), 'line' (折線圖)",
    )
    sql: str = Field(..., description="SQL query")
    wren_ai_thread_id: Optional[str] = Field(
        None, description="Wren AI thread ID for the request"
    )
    si_id: int = Field(..., description="SI ID for permission check")
    org_id: int = Field(
        ..., description="Organization ID to look up chatbot credentials"
    )
    thread_id: Optional[str] = Field(
        None, description="System thread UUID for artifact creation"
    )
    message_id: Optional[str] = Field(
        None, description="Message UUID to attach artifact to"
    )
    title: Optional[str] = Field(
        None, description="Artifact title, required when message_id is provided"
    )


class QueryTablesRequestDTO(BaseModel):
    query: str = Field(..., description="SQL string to query tables")


class QueryTableMessageResponseDTO(BaseModel):
    message: str
    total_rows: int


class ChatbotReadDTO(BaseModel):
    id: int
    name: str


class ArtifactReadDTO(BaseModel):
    id: str
    thread_id: str
    message_id: str
    type: str
    title: Optional[str] = None
    spec_json: Optional[Any] = None
    data_json: Optional[Any] = None
    storage_url: Optional[str] = None
    created_at: datetime


class ArtifactSummaryDTO(BaseModel):
    id: str
    message_id: str
    type: str
    title: Optional[str] = None


class MessageReadDTO(BaseModel):
    id: str
    thread_id: str
    seq: int
    role: str
    content_type: str
    content_text: Optional[str]
    content_json: Optional[Any]
    status: str
    parent_message_id: Optional[str]
    created_at: datetime
    artifacts: List[ArtifactSummaryDTO]


class ThreadSummaryDTO(BaseModel):
    id: str
    wren_thread_id: str
    title: str


class MessagePageDTO(BaseModel):
    next_cursor: Optional[str] = None


class MessageListResponseDTO(BaseModel):
    thread: ThreadSummaryDTO
    items: List[MessageReadDTO]
    page: MessagePageDTO


class ThreadReadDTO(BaseModel):
    id: str
    wren_ai_thread_id: str
    org_id: int
    user_id: int
    chatbot_id: int
    title: str
    last_message_at: Optional[datetime]
    message_count: int
    created_at: datetime
    updated_at: datetime


class ThreadPageDTO(BaseModel):
    next_cursor: Optional[str] = None


class ThreadListResponseDTO(BaseModel):
    items: List[ThreadReadDTO]
    page: ThreadPageDTO


class RenameThreadRequestDTO(BaseModel):
    title: str = Field(..., description="New thread title")


class ChatbotCsvReadDTO(BaseModel):
    id: int
    chatbot_id: int
    gcs_url: str
    original_filename: str
    created_at: datetime
    is_success: bool


class CsvUploadResponseDTO(BaseModel):
    gcs_url: str
    original_filename: str


class WrenCloudProjectDTO(BaseModel):
    id: int
    type: Optional[str] = None
    displayName: str
    createdAt: datetime
    updatedAt: datetime
    connectionInfo: Any | None = None
    language: str
    timezone: str


class WrenCloudProjectResponseDTO(BaseModel):
    project: WrenCloudProjectDTO
    status: str


class WrenCloudKeyResponseDTO(BaseModel):
    id: int
    name: str
    secret: str
    projectId: Any
    createdAt: str


class WrenSetupResponseDTO(BaseModel):
    id: int
    name: str
    org_id: int
    wren_project_id: str
    wren_api_key: str


class CsvTemplateType(str, Enum):
    GOOGLE_ADS = "google_ads"
    META_ADS = "meta_ads"


class DownloadCsvTemplateRequestDTO(BaseModel):
    types: List[CsvTemplateType] = Field(
        ..., min_length=1, description="CSV template types to download"
    )


class UpsertModelResponseDTO(BaseModel):
    success_table_names: List[str]
    dataset_id: str
    status: str
    success_count: int
