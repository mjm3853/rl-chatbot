import type { HealthResponse } from '../types/api';
import { get } from './client';

export async function getHealth(): Promise<HealthResponse> {
  return get<HealthResponse>('/api/v1/health');
}
