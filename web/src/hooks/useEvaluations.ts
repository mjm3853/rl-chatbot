import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as evaluationsApi from '../api/evaluations';
import type { EvaluationRequest } from '../types/api';

export function useEvaluations(agentId?: string) {
  return useQuery({
    queryKey: ['evaluations', { agentId }],
    queryFn: () => evaluationsApi.listEvaluations(agentId),
  });
}

export function useEvaluation(id: string) {
  return useQuery({
    queryKey: ['evaluations', id],
    queryFn: () => evaluationsApi.getEvaluation(id),
    enabled: !!id,
  });
}

export function useStartEvaluation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: EvaluationRequest) => evaluationsApi.startEvaluation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluations'] });
    },
  });
}
