import type { Agent, AgentCreate, AgentUpdate } from '../types/api';
import { get, post, patch, del } from './client';

export async function listAgents(activeOnly = true): Promise<Agent[]> {
  return get<Agent[]>(`/api/v1/agents?active_only=${activeOnly}`);
}

export async function getAgent(id: string): Promise<Agent> {
  return get<Agent>(`/api/v1/agents/${id}`);
}

export async function createAgent(data: AgentCreate): Promise<Agent> {
  return post<Agent>('/api/v1/agents', data);
}

export async function updateAgent(id: string, data: AgentUpdate): Promise<Agent> {
  return patch<Agent>(`/api/v1/agents/${id}`, data);
}

export async function deleteAgent(id: string): Promise<void> {
  return del(`/api/v1/agents/${id}`);
}

export async function resetAgent(id: string): Promise<Agent> {
  return post<Agent>(`/api/v1/agents/${id}/reset`);
}
