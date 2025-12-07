"""Test case CRUD endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..database import get_session
from ..models import TestCase, TestCaseCreate, TestCaseRead

router = APIRouter()


class TestCaseUpdate(BaseModel):
    """Schema for updating a test case."""

    name: Optional[str] = None
    user_input: Optional[str] = None
    expected_output: Optional[str] = None
    expected_tools_json: Optional[List[str]] = None
    task_type: Optional[str] = None
    is_active: Optional[bool] = None


class BulkTestCaseCreate(BaseModel):
    """Schema for bulk creating test cases."""

    test_cases: List[TestCaseCreate]


@router.post("", response_model=TestCaseRead, status_code=status.HTTP_201_CREATED)
async def create_test_case(
    test_case_data: TestCaseCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new test case."""
    test_case = TestCase(**test_case_data.model_dump())
    session.add(test_case)
    await session.commit()
    await session.refresh(test_case)
    return test_case


@router.post("/bulk", response_model=List[TestCaseRead], status_code=status.HTTP_201_CREATED)
async def bulk_create_test_cases(
    bulk_data: BulkTestCaseCreate,
    session: AsyncSession = Depends(get_session),
):
    """Bulk create test cases from a list."""
    test_cases = [TestCase(**tc.model_dump()) for tc in bulk_data.test_cases]
    session.add_all(test_cases)
    await session.commit()
    for tc in test_cases:
        await session.refresh(tc)
    return test_cases


@router.get("", response_model=List[TestCaseRead])
async def list_test_cases(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    session: AsyncSession = Depends(get_session),
):
    """List all test cases."""
    query = select(TestCase)
    if active_only:
        query = query.where(TestCase.is_active == True)
    query = query.offset(skip).limit(limit).order_by(TestCase.created_at.desc())
    result = await session.execute(query)
    return list(result.scalars().all())


@router.get("/{test_case_id}", response_model=TestCaseRead)
async def get_test_case(
    test_case_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a test case by ID."""
    result = await session.execute(select(TestCase).where(TestCase.id == test_case_id))
    test_case = result.scalar_one_or_none()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return test_case


@router.patch("/{test_case_id}", response_model=TestCaseRead)
async def update_test_case(
    test_case_id: UUID,
    test_case_data: TestCaseUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a test case."""
    result = await session.execute(select(TestCase).where(TestCase.id == test_case_id))
    test_case = result.scalar_one_or_none()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    update_data = test_case_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(test_case, key, value)

    session.add(test_case)
    await session.commit()
    await session.refresh(test_case)
    return test_case


@router.delete("/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_case(
    test_case_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete a test case (soft delete)."""
    result = await session.execute(select(TestCase).where(TestCase.id == test_case_id))
    test_case = result.scalar_one_or_none()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    test_case.is_active = False
    session.add(test_case)
    await session.commit()
    return None
