import type { Conversation, ConversationListItem } from '../types/api';
import { get, post, del } from './client';

export async function listConversations(agentId?: string): Promise<ConversationListItem[]> {
  const params = agentId ? `?agent_id=${agentId}` : '';
  return get<ConversationListItem[]>(`/api/v1/conversations${params}`);
}

export async function getConversation(id: string): Promise<Conversation> {
  return get<Conversation>(`/api/v1/conversations/${id}`);
}

export async function deleteConversation(id: string): Promise<void> {
  return del(`/api/v1/conversations/${id}`);
}

export async function endConversation(id: string): Promise<void> {
  return post(`/api/v1/conversations/${id}/end`);
}
