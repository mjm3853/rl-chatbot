import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as trainingApi from '../api/training';
import type { TrainingRequest } from '../types/api';

export function useTrainingRuns(agentId?: string) {
  return useQuery({
    queryKey: ['training', { agentId }],
    queryFn: () => trainingApi.listTrainingRuns(agentId),
  });
}

export function useTrainingRun(id: string) {
  return useQuery({
    queryKey: ['training', id],
    queryFn: () => trainingApi.getTrainingRun(id),
    enabled: !!id,
  });
}

export function useStartTraining() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TrainingRequest) => trainingApi.startTraining(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['training'] });
    },
  });
}

export function useStopTraining() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => trainingApi.stopTraining(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['training'] });
    },
  });
}
