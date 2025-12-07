"""Training database models."""

from datetime import datetime
from typing import Optional, List, Any, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .agent import Agent


class TrainingEpisodeBase(SQLModel):
    """Base training episode model."""

    episode_num: int
    avg_reward: float
    total_reward: float
    num_test_cases: int
    states_json: Optional[List[dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    actions_json: Optional[List[dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    rewards_json: Optional[List[float]] = Field(default=None, sa_column=Column(JSON))


class TrainingEpisode(TrainingEpisodeBase, table=True):
    """Database model for training episodes."""

    __tablename__ = "training_episodes"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    training_run_id: UUID = Field(foreign_key="training_runs.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    training_run: "TrainingRun" = Relationship(back_populates="episodes")


class TrainingRunBase(SQLModel):
    """Base training run model."""

    status: str = Field(default="pending", max_length=20)
    num_episodes: int
    current_episode: int = Field(default=0)
    final_avg_reward: Optional[float] = None
    config_json: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))


class TrainingRun(TrainingRunBase, table=True):
    """Database model for training runs."""

    __tablename__ = "training_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agent_id: UUID = Field(foreign_key="agents.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Relationships
    agent: "Agent" = Relationship(back_populates="training_runs")
    episodes: List[TrainingEpisode] = Relationship(back_populates="training_run")


class TrainingEpisodeRead(TrainingEpisodeBase):
    """Schema for reading a training episode."""

    id: UUID
    training_run_id: UUID
    created_at: datetime


class TrainingRunRead(TrainingRunBase):
    """Schema for reading a training run."""

    id: UUID
    agent_id: UUID
    started_at: datetime
    completed_at: Optional[datetime]
    episodes: List[TrainingEpisodeRead] = []
