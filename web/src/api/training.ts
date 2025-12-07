import type { TrainingRun, TrainingRunListItem, TrainingRequest } from '../types/api';
import { get, post } from './client';

export async function listTrainingRuns(agentId?: string): Promise<TrainingRunListItem[]> {
  const params = agentId ? `?agent_id=${agentId}` : '';
  return get<TrainingRunListItem[]>(`/api/v1/training${params}`);
}

export async function getTrainingRun(id: string): Promise<TrainingRun> {
  return get<TrainingRun>(`/api/v1/training/${id}`);
}

export async function startTraining(data: TrainingRequest): Promise<TrainingRunListItem> {
  return post<TrainingRunListItem>('/api/v1/training', data);
}

export async function stopTraining(id: string): Promise<void> {
  return post(`/api/v1/training/${id}/stop`);
}
