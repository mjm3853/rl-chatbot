"""Evaluation API schemas."""

from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel


class EvaluationRequest(BaseModel):
    """Schema for starting an evaluation."""

    agent_id: UUID
    test_case_ids: Optional[List[UUID]] = None  # If None, use all active test cases


class EvaluationProgress(BaseModel):
    """Schema for evaluation progress updates."""

    run_id: UUID
    status: str  # pending, running, completed, failed
    current_test_case: int
    total_test_cases: int
    progress_percent: int
    message: Optional[str] = None


class EvaluationResultRead(BaseModel):
    """Schema for reading an evaluation result."""

    id: UUID
    test_case_id: UUID
    task_success: float
    tool_usage_efficiency: float
    response_quality: float
    reward: float
    response_text: Optional[str]
    tool_calls_json: Optional[List[dict[str, Any]]]

    model_config = {"from_attributes": True}


class EvaluationRunRead(BaseModel):
    """Schema for reading an evaluation run."""

    id: UUID
    agent_id: UUID
    status: str
    num_test_cases: int
    started_at: datetime
    completed_at: Optional[datetime]
    aggregate_metrics_json: Optional[dict[str, float]]
    results: List[EvaluationResultRead] = []

    model_config = {"from_attributes": True}


class EvaluationRunListItem(BaseModel):
    """Schema for evaluation run list item."""

    id: UUID
    agent_id: UUID
    status: str
    num_test_cases: int
    started_at: datetime
    completed_at: Optional[datetime]
    aggregate_metrics_json: Optional[dict[str, float]]

    model_config = {"from_attributes": True}
