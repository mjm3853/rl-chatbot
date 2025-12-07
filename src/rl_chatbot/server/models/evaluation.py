"""Evaluation database models."""

from datetime import datetime
from typing import Optional, List, Any, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .agent import Agent


class TestCaseBase(SQLModel):
    """Base test case model."""

    name: Optional[str] = Field(default=None, max_length=255)
    user_input: str
    expected_output: Optional[str] = None
    expected_tools_json: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    task_type: str = Field(default="exact_match", max_length=50)
    is_active: bool = Field(default=True)


class TestCase(TestCaseBase, table=True):
    """Database model for test cases."""

    __tablename__ = "test_cases"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TestCaseCreate(TestCaseBase):
    """Schema for creating a test case."""

    pass


class TestCaseRead(TestCaseBase):
    """Schema for reading a test case."""

    id: UUID
    created_at: datetime


class EvaluationResultBase(SQLModel):
    """Base evaluation result model."""

    task_success: float
    tool_usage_efficiency: float
    response_quality: float
    reward: float
    response_text: Optional[str] = None
    tool_calls_json: Optional[List[dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))


class EvaluationResult(EvaluationResultBase, table=True):
    """Database model for evaluation results."""

    __tablename__ = "evaluation_results"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    evaluation_run_id: UUID = Field(foreign_key="evaluation_runs.id")
    test_case_id: UUID = Field(foreign_key="test_cases.id")

    # Relationships
    evaluation_run: "EvaluationRun" = Relationship(back_populates="results")


class EvaluationRunBase(SQLModel):
    """Base evaluation run model."""

    status: str = Field(default="pending", max_length=20)
    num_test_cases: int = Field(default=0)


class EvaluationRun(EvaluationRunBase, table=True):
    """Database model for evaluation runs."""

    __tablename__ = "evaluation_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agent_id: UUID = Field(foreign_key="agents.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    aggregate_metrics_json: Optional[dict[str, float]] = Field(default=None, sa_column=Column(JSON))

    # Relationships
    agent: "Agent" = Relationship(back_populates="evaluation_runs")
    results: List[EvaluationResult] = Relationship(back_populates="evaluation_run")


class EvaluationResultRead(EvaluationResultBase):
    """Schema for reading an evaluation result."""

    id: UUID
    evaluation_run_id: UUID
    test_case_id: UUID


class EvaluationRunRead(EvaluationRunBase):
    """Schema for reading an evaluation run."""

    id: UUID
    agent_id: UUID
    started_at: datetime
    completed_at: Optional[datetime]
    aggregate_metrics_json: Optional[dict[str, float]]
    results: List[EvaluationResultRead] = []
