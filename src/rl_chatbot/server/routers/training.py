"""Training endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session, async_session
from ..schemas.training import (
    TrainingRequest,
    TrainingRunRead,
    TrainingRunListItem,
    TrainingEpisodeRead,
)
from ..services.training_service import TrainingService
from ..websocket.manager import manager

router = APIRouter()


@router.post("/", response_model=TrainingRunListItem)
async def start_training(
    request: TrainingRequest,
    session: AsyncSession = Depends(get_session),
):
    """Start a new training run.

    The training runs in the background. Connect to the WebSocket endpoint
    to receive progress updates.
    """
    service = TrainingService(session)
    try:
        run = await service.start_training(request)
        return TrainingRunListItem(
            id=run.id,
            agent_id=run.agent_id,
            status=run.status,
            num_episodes=run.num_episodes,
            current_episode=run.current_episode,
            final_avg_reward=run.final_avg_reward,
            started_at=run.started_at,
            completed_at=run.completed_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[TrainingRunListItem])
async def list_training_runs(
    agent_id: Optional[UUID] = Query(None, description="Filter by agent ID"),
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """List training runs."""
    service = TrainingService(session)
    runs = await service.list_runs(agent_id=agent_id, skip=skip, limit=limit)
    return [
        TrainingRunListItem(
            id=run.id,
            agent_id=run.agent_id,
            status=run.status,
            num_episodes=run.num_episodes,
            current_episode=run.current_episode,
            final_avg_reward=run.final_avg_reward,
            started_at=run.started_at,
            completed_at=run.completed_at,
        )
        for run in runs
    ]


@router.get("/{run_id}", response_model=TrainingRunRead)
async def get_training_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a training run with all episodes."""
    service = TrainingService(session)
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")

    return TrainingRunRead(
        id=run.id,
        agent_id=run.agent_id,
        status=run.status,
        num_episodes=run.num_episodes,
        current_episode=run.current_episode,
        final_avg_reward=run.final_avg_reward,
        config_json=run.config_json,
        started_at=run.started_at,
        completed_at=run.completed_at,
        episodes=[
            TrainingEpisodeRead(
                id=e.id,
                episode_num=e.episode_num,
                avg_reward=e.avg_reward,
                total_reward=e.total_reward,
                num_test_cases=e.num_test_cases,
                created_at=e.created_at,
            )
            for e in sorted(run.episodes, key=lambda x: x.episode_num)
        ],
    )


@router.post("/{run_id}/stop")
async def stop_training(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Stop a running training."""
    service = TrainingService(session)
    success = await service.stop_training(run_id)
    if success:
        return {"status": "stopping", "run_id": str(run_id)}
    raise HTTPException(status_code=404, detail="Training run not found or not running")


@router.websocket("/ws/{run_id}")
async def training_progress_websocket(
    websocket: WebSocket,
    run_id: UUID,
):
    """WebSocket endpoint for training progress updates.

    Connect to ws://host/api/v1/training/ws/{run_id}

    Receive updates as JSON:
    - {"run_id": "...", "status": "running", "progress_percent": 50, ...}
    """
    await manager.connect_progress(websocket, run_id)
    try:
        while True:
            # Keep connection alive, wait for disconnect
            await websocket.receive_text()
    except Exception:
        manager.disconnect_progress(websocket, run_id)
