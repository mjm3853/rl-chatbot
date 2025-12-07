"""Training API schemas."""

from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel


class TrainingRequest(BaseModel):
    """Schema for starting a training run."""

    agent_id: UUID
    num_episodes: int = 10
    test_case_ids: Optional[List[UUID]] = None  # If None, use all active test cases
    reward_weights: Optional[dict[str, float]] = None  # Custom reward weights


class TrainingProgress(BaseModel):
    """Schema for training progress updates."""

    run_id: UUID
    status: str  # pending, running, completed, failed, cancelled
    current_episode: int
    total_episodes: int
    progress_percent: int
    current_avg_reward: Optional[float] = None
    message: Optional[str] = None


class TrainingEpisodeRead(BaseModel):
    """Schema for reading a training episode."""

    id: UUID
    episode_num: int
    avg_reward: float
    total_reward: float
    num_test_cases: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TrainingRunRead(BaseModel):
    """Schema for reading a training run."""

    id: UUID
    agent_id: UUID
    status: str
    num_episodes: int
    current_episode: int
    final_avg_reward: Optional[float]
    config_json: Optional[dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]
    episodes: List[TrainingEpisodeRead] = []

    model_config = {"from_attributes": True}


class TrainingRunListItem(BaseModel):
    """Schema for training run list item."""

    id: UUID
    agent_id: UUID
    status: str
    num_episodes: int
    current_episode: int
    final_avg_reward: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}
