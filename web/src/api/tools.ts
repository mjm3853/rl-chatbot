import type { Tool } from '../types/api';
import { get } from './client';

export async function listTools(): Promise<Tool[]> {
  return get<Tool[]>('/api/v1/tools');
}
