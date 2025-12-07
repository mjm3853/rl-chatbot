import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as conversationsApi from '../api/conversations';

export function useConversations(agentId?: string) {
  return useQuery({
    queryKey: ['conversations', { agentId }],
    queryFn: () => conversationsApi.listConversations(agentId),
  });
}

export function useConversation(id: string) {
  return useQuery({
    queryKey: ['conversations', id],
    queryFn: () => conversationsApi.getConversation(id),
    enabled: !!id,
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => conversationsApi.deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}
