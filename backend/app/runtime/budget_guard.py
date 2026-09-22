from dataclasses import dataclass

from app.domain.run_state import RunState


class BudgetExceededError(Exception):
    def __init__(
        self,
        limit_name: str,
        limit: int | float,
        used: int | float,
        requested: int | float,
    ) -> None:
        self.limit_name = limit_name
        self.limit = limit
        self.used = used
        self.requested = requested
        super().__init__(
            f"{limit_name} budget exceeded: "
            f"used={used}, requested={requested}, limit={limit}"
        )


@dataclass(frozen=True)
class RemainingBudget:
    steps: int
    llm_calls: int
    tool_calls: int
    tokens: int
    cost_usd: float


class BudgetGuard:
    def check_step(self, state: RunState, requested: int = 1) -> None:
        self._validate_non_negative("requested", requested)
        self._check_limit(
            "Step",
            state.budget.max_steps,
            state.steps_used,
            requested,
        )

    def check_llm_call(
        self,
        state: RunState,
        requested_calls: int = 1,
        requested_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
    ) -> None:
        self._validate_non_negative("requested_calls", requested_calls)
        self._validate_non_negative("requested_tokens", requested_tokens)
        self._validate_non_negative("estimated_cost_usd", estimated_cost_usd)
        self._check_limit(
            "LLM call",
            state.budget.max_llm_calls,
            state.llm_calls_used,
            requested_calls,
        )
        self._check_limit(
            "Token",
            state.budget.max_tokens,
            state.tokens_used,
            requested_tokens,
        )
        self._check_limit(
            "Cost",
            state.budget.max_cost_usd,
            state.cost_usd,
            estimated_cost_usd,
        )

    def check_tool_call(self, state: RunState, requested: int = 1) -> None:
        self._validate_non_negative("requested", requested)
        self._check_limit(
            "Tool call",
            state.budget.max_tool_calls,
            state.tool_calls_used,
            requested,
        )

    def record_step(self, state: RunState, used: int = 1) -> None:
        self._validate_non_negative("used", used)
        state.steps_used += used

    def record_llm_call(
        self,
        state: RunState,
        calls: int = 1,
        tokens: int = 0,
        actual_cost_usd: float = 0.0,
    ) -> None:
        self._validate_non_negative("calls", calls)
        self._validate_non_negative("tokens", tokens)
        self._validate_non_negative("actual_cost_usd", actual_cost_usd)
        state.llm_calls_used += calls
        state.tokens_used += tokens
        state.cost_usd += actual_cost_usd

    def record_tool_call(self, state: RunState, used: int = 1) -> None:
        self._validate_non_negative("used", used)
        state.tool_calls_used += used

    def remaining(self, state: RunState) -> RemainingBudget:
        return RemainingBudget(
            steps=max(0, state.budget.max_steps - state.steps_used),
            llm_calls=max(0, state.budget.max_llm_calls - state.llm_calls_used),
            tool_calls=max(0, state.budget.max_tool_calls - state.tool_calls_used),
            tokens=max(0, state.budget.max_tokens - state.tokens_used),
            cost_usd=max(0.0, state.budget.max_cost_usd - state.cost_usd),
        )

    @staticmethod
    def _check_limit(
        limit_name: str,
        limit: int | float,
        used: int | float,
        requested: int | float,
    ) -> None:
        if used + requested > limit:
            raise BudgetExceededError(limit_name, limit, used, requested)

    @staticmethod
    def _validate_non_negative(name: str, value: int | float) -> None:
        if value < 0:
            raise ValueError(f"{name} must not be negative")
