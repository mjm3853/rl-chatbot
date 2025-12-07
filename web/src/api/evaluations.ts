import type { EvaluationRun, EvaluationRunListItem, EvaluationRequest } from '../types/api';
import { get, post } from './client';

export async function listEvaluations(agentId?: string): Promise<EvaluationRunListItem[]> {
  const params = agentId ? `?agent_id=${agentId}` : '';
  return get<EvaluationRunListItem[]>(`/api/v1/evaluations${params}`);
}

export async function getEvaluation(id: string): Promise<EvaluationRun> {
  return get<EvaluationRun>(`/api/v1/evaluations/${id}`);
}

export async function startEvaluation(data: EvaluationRequest): Promise<EvaluationRunListItem> {
  return post<EvaluationRunListItem>('/api/v1/evaluations', data);
}
