import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import * as chatApi from '../api/chat';
import type { ChatResponse, ToolCall } from '../types/api';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
}

export function useChat(agentId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const sendMessage = useMutation({
    mutationFn: async (message: string) => {
      if (!agentId) throw new Error('No agent selected');
      return chatApi.sendMessage({
        agent_id: agentId,
        message,
        conversation_id: conversationId || undefined,
      });
    },
    onMutate: (message) => {
      // Optimistically add user message
      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: message,
      };
      setMessages((prev) => [...prev, userMsg]);
    },
    onSuccess: (response: ChatResponse) => {
      setConversationId(response.conversation_id);
      const assistantMsg: ChatMessage = {
        id: response.message_id,
        role: 'assistant',
        content: response.response,
        toolCalls: response.tool_calls,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    },
  });

  const resetChat = useCallback(() => {
    setMessages([]);
    setConversationId(null);
  }, []);

  return {
    messages,
    conversationId,
    sendMessage: sendMessage.mutate,
    isPending: sendMessage.isPending,
    error: sendMessage.error,
    resetChat,
  };
}
