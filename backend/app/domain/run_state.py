from enum import Enum

from pydantic import BaseModel, Field, JsonValue, PositiveFloat, PositiveInt


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SourceType(str, Enum):
    INTERNAL_KNOWLEDGE = "internal_knowledge"
    WEB = "web"
    TOOL = "tool"
    MEMORY = "memory"


class RiskLevel(str, Enum):
    READ_ONLY = "read_only"
    REVERSIBLE = "reversible"
    IRREVERSIBLE = "irreversible"


class MemoryType(str, Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"


class RunBudget(BaseModel):
    max_steps: PositiveInt
    max_llm_calls: PositiveInt
    max_tool_calls: PositiveInt
    max_tokens: PositiveInt
    max_cost_usd: PositiveFloat
    timeout_seconds: PositiveInt


class PlannedStep(BaseModel):
    step_id: str
    objective: str
    status: StepStatus = StepStatus.PENDING
    allowed_tools: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.READ_ONLY


class EvidenceRef(BaseModel):
    evidence_id: str
    source_type: SourceType
    title: str
    uri: str | None = None
    score: float = Field(ge=0)
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class MemoryRef(BaseModel):
    memory_id: str
    memory_type: MemoryType
    relevance_score: float = Field(ge=0)


class FailureRecord(BaseModel):
    step_id: str
    error_type: str
    message: str
    attempt: PositiveInt
    retryable: bool


class ApprovalRequest(BaseModel):
    step_id: str
    tool_name: str
    arguments: dict[str, JsonValue] = Field(default_factory=dict)
    risk_level: RiskLevel
    reason: str


class RunState(BaseModel):
    run_id: str
    user_query: str
    status: RunStatus = RunStatus.PENDING
    current_step_id: str | None = None
    plan: list[PlannedStep] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    memory_refs: list[MemoryRef] = Field(default_factory=list)
    failures: list[FailureRecord] = Field(default_factory=list)
    budget: RunBudget
    pending_approval: ApprovalRequest | None = None
    steps_used: int = Field(default=0, ge=0)
    llm_calls_used: int = Field(default=0, ge=0)
    tool_calls_used: int = Field(default=0, ge=0)
    tokens_used: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0, ge=0)
