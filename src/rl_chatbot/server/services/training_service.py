"""Training service for running agent training."""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from ..models import Agent, TestCase, TrainingRun, TrainingEpisode
from ..schemas.training import TrainingRequest, TrainingProgress
from ..websocket.manager import manager

from rl_chatbot.factory import AgentFactory
from rl_chatbot.rl.trainer import RLTrainer
from rl_chatbot.rl.reward import RewardFunction


class TrainingService:
    """Service for running training."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._factory = AgentFactory()
        self._running_tasks: Dict[UUID, asyncio.Task] = {}
        self._cancelled_runs: set = set()

    async def start_training(self, request: TrainingRequest) -> TrainingRun:
        """Start a new training run."""
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

        # Create training run
        run = TrainingRun(
            agent_id=request.agent_id,
            status="pending",
            num_episodes=request.num_episodes,
            current_episode=0,
            config_json={
                "reward_weights": request.reward_weights,
                "test_case_count": len(test_cases),
            },
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)

        # Start background task
        task = asyncio.create_task(
            self._run_training(run.id, agent_db, test_cases, request)
        )
        self._running_tasks[run.id] = task

        return run

    async def stop_training(self, run_id: UUID) -> bool:
        """Stop a running training."""
        if run_id in self._running_tasks:
            self._cancelled_runs.add(run_id)
            self._running_tasks[run_id].cancel()
            return True
        return False

    async def _run_training(
        self,
        run_id: UUID,
        agent_db: Agent,
        test_cases: List[TestCase],
        request: TrainingRequest,
    ):
        """Run training in background."""
        from ..database import async_session

        async with async_session() as session:
            try:
                # Update status to running
                result = await session.execute(
                    select(TrainingRun).where(TrainingRun.id == run_id)
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

                # Create reward function with custom weights if provided
                reward_function = RewardFunction()
                if request.reward_weights:
                    reward_function.weights = request.reward_weights

                # Convert test cases to dict format
                test_case_dicts = [
                    {
                        "user_input": tc.user_input,
                        "expected_output": tc.expected_output,
                        "expected_tools": tc.expected_tools_json or [],
                        "task_type": tc.task_type,
                    }
                    for tc in test_cases
                ]

                # Run training episodes
                total_avg_reward = 0.0

                for episode in range(request.num_episodes):
                    # Check for cancellation
                    if run_id in self._cancelled_runs:
                        raise asyncio.CancelledError()

                    # Send progress update
                    progress = TrainingProgress(
                        run_id=run_id,
                        status="running",
                        current_episode=episode + 1,
                        total_episodes=request.num_episodes,
                        progress_percent=int((episode / request.num_episodes) * 100),
                        message=f"Running episode {episode + 1}/{request.num_episodes}",
                    )
                    await manager.send_progress(run_id, progress.model_dump())

                    # Collect episode rewards
                    episode_rewards = []
                    for tc_dict in test_case_dicts:
                        agent.reset()
                        response = agent.chat(tc_dict["user_input"])
                        tool_calls = agent.get_last_tool_calls()

                        reward = reward_function.compute_reward(
                            agent=agent,
                            user_input=tc_dict["user_input"],
                            expected_output=tc_dict.get("expected_output"),
                            expected_tools=tc_dict.get("expected_tools", []),
                            task_type=tc_dict.get("task_type", "contains"),
                        )
                        episode_rewards.append(reward)

                    # Calculate episode metrics
                    avg_reward = sum(episode_rewards) / len(episode_rewards)
                    total_reward = sum(episode_rewards)
                    total_avg_reward += avg_reward

                    # Save episode
                    training_episode = TrainingEpisode(
                        training_run_id=run_id,
                        episode_num=episode,
                        avg_reward=avg_reward,
                        total_reward=total_reward,
                        num_test_cases=len(test_case_dicts),
                        rewards_json=episode_rewards,
                    )
                    session.add(training_episode)

                    # Update run progress
                    result = await session.execute(
                        select(TrainingRun).where(TrainingRun.id == run_id)
                    )
                    run = result.scalar_one()
                    run.current_episode = episode + 1
                    session.add(run)
                    await session.commit()

                    # Send progress with reward
                    progress = TrainingProgress(
                        run_id=run_id,
                        status="running",
                        current_episode=episode + 1,
                        total_episodes=request.num_episodes,
                        progress_percent=int(((episode + 1) / request.num_episodes) * 100),
                        current_avg_reward=avg_reward,
                        message=f"Episode {episode + 1} complete, avg reward: {avg_reward:.3f}",
                    )
                    await manager.send_progress(run_id, progress.model_dump())

                # Calculate final metrics
                final_avg_reward = total_avg_reward / request.num_episodes

                # Update run as completed
                result = await session.execute(
                    select(TrainingRun).where(TrainingRun.id == run_id)
                )
                run = result.scalar_one()
                run.status = "completed"
                run.completed_at = datetime.utcnow()
                run.final_avg_reward = final_avg_reward
                session.add(run)
                await session.commit()

                # Send completion update
                progress = TrainingProgress(
                    run_id=run_id,
                    status="completed",
                    current_episode=request.num_episodes,
                    total_episodes=request.num_episodes,
                    progress_percent=100,
                    current_avg_reward=final_avg_reward,
                    message=f"Training completed, final avg reward: {final_avg_reward:.3f}",
                )
                await manager.send_progress(run_id, progress.model_dump())

            except asyncio.CancelledError:
                # Update run as cancelled
                result = await session.execute(
                    select(TrainingRun).where(TrainingRun.id == run_id)
                )
                run = result.scalar_one()
                run.status = "cancelled"
                run.completed_at = datetime.utcnow()
                session.add(run)
                await session.commit()

                # Send cancellation update
                progress = TrainingProgress(
                    run_id=run_id,
                    status="cancelled",
                    current_episode=run.current_episode,
                    total_episodes=request.num_episodes,
                    progress_percent=int((run.current_episode / request.num_episodes) * 100),
                    message="Training cancelled",
                )
                await manager.send_progress(run_id, progress.model_dump())

            except Exception as e:
                # Update run as failed
                result = await session.execute(
                    select(TrainingRun).where(TrainingRun.id == run_id)
                )
                run = result.scalar_one()
                run.status = "failed"
                run.completed_at = datetime.utcnow()
                session.add(run)
                await session.commit()

                # Send failure update
                progress = TrainingProgress(
                    run_id=run_id,
                    status="failed",
                    current_episode=0,
                    total_episodes=request.num_episodes,
                    progress_percent=0,
                    message=f"Training failed: {str(e)}",
                )
                await manager.send_progress(run_id, progress.model_dump())

            finally:
                # Clean up
                if run_id in self._running_tasks:
                    del self._running_tasks[run_id]
                self._cancelled_runs.discard(run_id)

    async def get_run(self, run_id: UUID) -> Optional[TrainingRun]:
        """Get a training run with episodes."""
        result = await self.session.execute(
            select(TrainingRun)
            .where(TrainingRun.id == run_id)
            .options(selectinload(TrainingRun.episodes))
        )
        return result.scalar_one_or_none()

    async def list_runs(
        self,
        agent_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TrainingRun]:
        """List training runs."""
        query = select(TrainingRun)
        if agent_id:
            query = query.where(TrainingRun.agent_id == agent_id)
        query = query.offset(skip).limit(limit).order_by(TrainingRun.started_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
