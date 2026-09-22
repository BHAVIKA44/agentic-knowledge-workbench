from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, JsonValue, PositiveInt, model_validator

from app.domain.run_state import RiskLevel


class ToolResultStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, JsonValue] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.READ_ONLY
    timeout_seconds: PositiveInt
    retryable: bool = False
    tags: list[str] = Field(default_factory=list)


class ToolCallRequest(BaseModel):
    call_id: str
    step_id: str
    tool_name: str
    arguments: dict[str, JsonValue] = Field(default_factory=dict)


class ToolCallResult(BaseModel):
    call_id: str
    tool_name: str
    status: ToolResultStatus = ToolResultStatus.SUCCESS
    output: JsonValue | None = None
    error_code: str | None = None
    error_message: str | None = None
    latency_ms: float = Field(default=0, ge=0)
    retryable: bool = False

    @model_validator(mode="after")
    def validate_status_fields(self) -> Self:
        if self.status is ToolResultStatus.SUCCESS:
            if self.error_code is not None or self.error_message is not None:
                raise ValueError("successful tool results cannot contain errors")
        elif self.output is not None:
            raise ValueError("failed tool results cannot contain output")
        elif self.error_code is None and self.error_message is None:
            raise ValueError("failed tool results must contain an error")
        return self


class ToolContext(BaseModel):
    run_id: str
    step_id: str
    user_id: str | None = None
    request_id: str | None = None
