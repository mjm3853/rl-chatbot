import type { TestCase, TestCaseCreate, TestCaseUpdate } from '../types/api';
import { get, post, patch, del } from './client';

export async function listTestCases(activeOnly = true): Promise<TestCase[]> {
  return get<TestCase[]>(`/api/v1/test-cases?active_only=${activeOnly}`);
}

export async function getTestCase(id: string): Promise<TestCase> {
  return get<TestCase>(`/api/v1/test-cases/${id}`);
}

export async function createTestCase(data: TestCaseCreate): Promise<TestCase> {
  return post<TestCase>('/api/v1/test-cases', data);
}

export async function createTestCasesBulk(testCases: TestCaseCreate[]): Promise<TestCase[]> {
  return post<TestCase[]>('/api/v1/test-cases/bulk', { test_cases: testCases });
}

export async function updateTestCase(id: string, data: TestCaseUpdate): Promise<TestCase> {
  return patch<TestCase>(`/api/v1/test-cases/${id}`, data);
}

export async function deleteTestCase(id: string): Promise<void> {
  return del(`/api/v1/test-cases/${id}`);
}
