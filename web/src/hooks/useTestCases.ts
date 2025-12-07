import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as testCasesApi from '../api/testCases';
import type { TestCaseCreate, TestCaseUpdate } from '../types/api';

export function useTestCases(activeOnly = true) {
  return useQuery({
    queryKey: ['testCases', { activeOnly }],
    queryFn: () => testCasesApi.listTestCases(activeOnly),
  });
}

export function useTestCase(id: string) {
  return useQuery({
    queryKey: ['testCases', id],
    queryFn: () => testCasesApi.getTestCase(id),
    enabled: !!id,
  });
}

export function useCreateTestCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TestCaseCreate) => testCasesApi.createTestCase(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testCases'] });
    },
  });
}

export function useCreateTestCasesBulk() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (testCases: TestCaseCreate[]) => testCasesApi.createTestCasesBulk(testCases),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testCases'] });
    },
  });
}

export function useUpdateTestCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TestCaseUpdate }) =>
      testCasesApi.updateTestCase(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testCases'] });
    },
  });
}

export function useDeleteTestCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => testCasesApi.deleteTestCase(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testCases'] });
    },
  });
}
