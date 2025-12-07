import { useState, useRef, useEffect } from 'react';
import { useAgents } from '../hooks/useAgents';
import { useChat } from '../hooks/useChat';
import { Button, Select, Spinner } from '../components/common';
import type { ToolCall } from '../types/api';
import styles from './Chat.module.css';
import pageStyles from './Page.module.css';

export function Chat() {
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: agents, isLoading: agentsLoading } = useAgents();
  const { messages, conversationId, sendMessage, isPending, resetChat } = useChat(selectedAgentId);

  const agentOptions = [
    { value: '', label: '-- Select Agent --' },
    ...(agents?.map((a) => ({ value: a.id, label: a.name || a.id.slice(0, 8) })) ?? []),
  ];

  const handleSend = () => {
    if (!inputValue.trim() || !selectedAgentId || isPending) return;
    sendMessage(inputValue);
    setInputValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleAgentChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newId = e.target.value || null;
    setSelectedAgentId(newId);
    resetChat();
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className={pageStyles.page}>
      <header className={pageStyles.header}>
        <h1>CHAT</h1>
        <div className={styles.headerControls}>
          {agentsLoading ? (
            <Spinner size="sm" />
          ) : (
            <Select
              options={agentOptions}
              value={selectedAgentId || ''}
              onChange={handleAgentChange}
            />
          )}
          {conversationId && (
            <span className={styles.convId}>Conv: {conversationId.slice(0, 8)}</span>
          )}
          {messages.length > 0 && (
            <Button variant="ghost" size="sm" onClick={resetChat}>
              Clear
            </Button>
          )}
        </div>
      </header>

      <div className={styles.chatContainer}>
        <div className={styles.messages}>
          {messages.length === 0 ? (
            <div className={styles.emptyState}>
              {selectedAgentId
                ? 'Start a conversation by typing a message below.'
                : 'Select an agent to start chatting.'}
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`${styles.message} ${styles[msg.role]}`}>
                <div className={styles.messageHeader}>
                  <span className={styles.role}>{msg.role.toUpperCase()}</span>
                </div>
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className={styles.toolCalls}>
                    {msg.toolCalls.map((tc) => (
                      <ToolCallDisplay key={tc.id} toolCall={tc} />
                    ))}
                  </div>
                )}
                <div className={styles.messageContent}>{msg.content}</div>
              </div>
            ))
          )}
          {isPending && (
            <div className={styles.thinking}>
              <Spinner size="sm" /> Thinking...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className={styles.inputArea}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={selectedAgentId ? 'Type a message...' : 'Select an agent first'}
            disabled={!selectedAgentId || isPending}
            className={styles.input}
          />
          <Button
            variant="primary"
            onClick={handleSend}
            disabled={!selectedAgentId || !inputValue.trim() || isPending}
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}

function ToolCallDisplay({ toolCall }: { toolCall: ToolCall }) {
  return (
    <div className={styles.toolCall}>
      <div className={styles.toolHeader}>
        <span className={styles.toolName}>{toolCall.tool_name}</span>
        {toolCall.duration_ms && (
          <span className={styles.toolDuration}>{toolCall.duration_ms}ms</span>
        )}
      </div>
      <div className={styles.toolArgs}>
        {JSON.stringify(toolCall.arguments_json)}
      </div>
      {toolCall.result && (
        <div className={styles.toolResult}>
          <span className={styles.arrow}>&rarr;</span> {toolCall.result}
        </div>
      )}
    </div>
  );
}
