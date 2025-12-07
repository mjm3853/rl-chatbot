"""Evaluation service for running agent evaluations."""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from ..models import Agent, TestCase, EvaluationRun, EvaluationResult
from ..schemas.evaluation import EvaluationRequest, EvaluationProgress
from ..websocket.manager import manager

from rl_chatbot.factory import AgentFactory
from rl_chatbot.evaluation.evaluator import Evaluator


class EvaluationService:
    """Service for running evaluations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._factory = AgentFactory()
        self._running_tasks: Dict[UUID, asyncio.Task] = {}

    async def start_evaluation(self, request: EvaluationRequest) -> EvaluationRun:
        """Start a new evaluation run."""
        # Verify agent exists
        result = await self.session.execute(select(Agent).where(Agent.id == request.agent_id))
        agent_db = result.scalar_one_or_none()
        if not agent_db:
            raise ValueError(f"Agent {request.agent_id} not found")

        # Get test cases
        if request.test_case_ids:
            result = await self.session.execute(
                select(TestCase).where(
                    TestCase.id.in_(request.test_case_ids),
                    TestCase.is_active == True,
                )
            )
        else:
            result = await self.session.execute(
                select(TestCase).where(TestCase.is_active == True)
            )
        test_cases = list(result.scalars().all())

        if not test_cases:
            raise ValueError("No test cases found")

        # Create evaluation run
        run = EvaluationRun(
            agent_id=request.agent_id,
            status="pending",
            num_test_cases=len(test_cases),
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)

        # Start background task
        task = asyncio.create_task(
            self._run_evaluation(run.id, agent_db, test_cases)
        )
        self._running_tasks[run.id] = task

        return run

    async def _run_evaluation(
        self,
        run_id: UUID,
        agent_db: Agent,
        test_cases: List[TestCase],
    ):
        """Run evaluation in background."""
        # Need a new session for background task
        from ..database import async_session

        async with async_session() as session:
            try:
                # Update status to running
                result = await session.execute(
                    select(EvaluationRun).where(EvaluationRun.id == run_id)
                )
                run = result.scalar_one()
                run.status = "running"
                session.add(run)
                await session.commit()

                # Create in-memory agent
                agent = self._factory.create_agent(
                    agent_type=agent_db.agent_type,
                    model=agent_db.model,
                    temperature=agent_db.temperature,
                )

                # Create evaluator
                evaluator = Evaluator(agent)

                # Run evaluation for each test case
                total_metrics = {
                    "task_success": 0.0,
                    "tool_usage_efficiency": 0.0,
                    "response_quality": 0.0,
                    "reward": 0.0,
                }

                for i, test_case in enumerate(test_cases):
                    # Send progress update
                    progress = EvaluationProgress(
                        run_id=run_id,
                        status="running",
                        current_test_case=i + 1,
                        total_test_cases=len(test_cases),
                        progress_percent=int((i / len(test_cases)) * 100),
                        message=f"Evaluating test case {i + 1}/{len(test_cases)}",
                    )
                    await manager.send_progress(run_id, progress.model_dump())

                    # Reset agent for each test case
                    agent.reset()

                    # Run evaluation
                    metrics = evaluator.evaluate_single(
                        user_input=test_case.user_input,
                        expected_output=test_case.expected_output,
                        expected_tools=test_case.expected_tools_json or [],
                        task_type=test_case.task_type,
                    )

                    # Get tool calls
                    tool_calls = agent.get_last_tool_calls()

                    # Save result
                    eval_result = EvaluationResult(
                        evaluation_run_id=run_id,
                        test_case_id=test_case.id,
                        task_success=metrics.task_success,
                        tool_usage_efficiency=metrics.tool_usage_efficiency,
                        response_quality=metrics.response_quality,
                        reward=metrics.reward,
                        response_text=agent.chat(""),  # Get last response
                        tool_calls_json=tool_calls,
                    )
                    session.add(eval_result)

                    # Accumulate metrics
                    total_metrics["task_success"] += metrics.task_success
                    total_metrics["tool_usage_efficiency"] += metrics.tool_usage_efficiency
                    total_metrics["response_quality"] += metrics.response_quality
                    total_metrics["reward"] += metrics.reward

                await session.commit()

                # Calculate aggregate metrics
                n = len(test_cases)
                aggregate_metrics = {
                    k: v / n for k, v in total_metrics.items()
                }

                # Update run as completed
                result = await session.execute(
                    select(EvaluationRun).where(EvaluationRun.id == run_id)
                )
                run = result.scalar_one()
                run.status = "completed"
                run.completed_at = datetime.utcnow()
                run.aggregate_metrics_json = aggregate_metrics
                session.add(run)
                await session.commit()

                # Send completion update
                progress = EvaluationProgress(
                    run_id=run_id,
                    status="completed",
                    current_test_case=len(test_cases),
                    total_test_cases=len(test_cases),
                    progress_percent=100,
                    message="Evaluation completed",
                )
                await manager.send_progress(run_id, progress.model_dump())

            except Exception as e:
                # Update run as failed
                result = await session.execute(
                    select(EvaluationRun).where(EvaluationRun.id == run_id)
                )
                run = result.scalar_one()
                run.status = "failed"
                run.completed_at = datetime.utcnow()
                session.add(run)
                await session.commit()

                # Send failure update
                progress = EvaluationProgress(
                    run_id=run_id,
                    status="failed",
                    current_test_case=0,
                    total_test_cases=len(test_cases),
                    progress_percent=0,
                    message=f"Evaluation failed: {str(e)}",
                )
                await manager.send_progress(run_id, progress.model_dump())

            finally:
                # Clean up task reference
                if run_id in self._running_tasks:
                    del self._running_tasks[run_id]

    async def get_run(self, run_id: UUID) -> Optional[EvaluationRun]:
        """Get an evaluation run with results."""
        result = await self.session.execute(
            select(EvaluationRun)
            .where(EvaluationRun.id == run_id)
            .options(selectinload(EvaluationRun.results))
        )
        return result.scalar_one_or_none()

    async def list_runs(
        self,
        agent_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[EvaluationRun]:
        """List evaluation runs."""
        query = select(EvaluationRun)
        if agent_id:
            query = query.where(EvaluationRun.agent_id == agent_id)
        query = query.offset(skip).limit(limit).order_by(EvaluationRun.started_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
