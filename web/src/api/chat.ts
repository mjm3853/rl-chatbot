import type { ChatRequest, ChatResponse } from '../types/api';
import { post } from './client';

export async function sendMessage(data: ChatRequest): Promise<ChatResponse> {
  return post<ChatResponse>('/api/v1/chat', data);
}
