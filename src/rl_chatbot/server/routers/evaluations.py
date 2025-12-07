"""Evaluation endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session, async_session
from ..schemas.evaluation import (
    EvaluationRequest,
    EvaluationRunRead,
    EvaluationRunListItem,
    EvaluationResultRead,
)
from ..services.evaluation_service import EvaluationService
from ..websocket.manager import manager

router = APIRouter()


@router.post("", response_model=EvaluationRunListItem)
async def start_evaluation(
    request: EvaluationRequest,
    session: AsyncSession = Depends(get_session),
):
    """Start a new evaluation run.

    The evaluation runs in the background. Connect to the WebSocket endpoint
    to receive progress updates.
    """
    service = EvaluationService(session)
    try:
        run = await service.start_evaluation(request)
        return EvaluationRunListItem(
            id=run.id,
            agent_id=run.agent_id,
            status=run.status,
            num_test_cases=run.num_test_cases,
            started_at=run.started_at,
            completed_at=run.completed_at,
            aggregate_metrics_json=run.aggregate_metrics_json,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[EvaluationRunListItem])
async def list_evaluations(
    agent_id: Optional[UUID] = Query(None, description="Filter by agent ID"),
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """List evaluation runs."""
    service = EvaluationService(session)
    runs = await service.list_runs(agent_id=agent_id, skip=skip, limit=limit)
    return [
        EvaluationRunListItem(
            id=run.id,
            agent_id=run.agent_id,
            status=run.status,
            num_test_cases=run.num_test_cases,
            started_at=run.started_at,
            completed_at=run.completed_at,
            aggregate_metrics_json=run.aggregate_metrics_json,
        )
        for run in runs
    ]


@router.get("/{run_id}", response_model=EvaluationRunRead)
async def get_evaluation(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get an evaluation run with all results."""
    service = EvaluationService(session)
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")

    return EvaluationRunRead(
        id=run.id,
        agent_id=run.agent_id,
        status=run.status,
        num_test_cases=run.num_test_cases,
        started_at=run.started_at,
        completed_at=run.completed_at,
        aggregate_metrics_json=run.aggregate_metrics_json,
        results=[
            EvaluationResultRead(
                id=r.id,
                test_case_id=r.test_case_id,
                task_success=r.task_success,
                tool_usage_efficiency=r.tool_usage_efficiency,
                response_quality=r.response_quality,
                reward=r.reward,
                response_text=r.response_text,
                tool_calls_json=r.tool_calls_json,
            )
            for r in run.results
        ],
    )


@router.websocket("/ws/{run_id}")
async def evaluation_progress_websocket(
    websocket: WebSocket,
    run_id: UUID,
):
    """WebSocket endpoint for evaluation progress updates.

    Connect to ws://host/api/v1/evaluations/ws/{run_id}

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
