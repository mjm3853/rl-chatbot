import { useState } from 'react';
import { useConversations, useConversation, useDeleteConversation } from '../hooks/useConversations';
import { useAgents } from '../hooks/useAgents';
import { Button, Table, Badge, Select, Spinner, Modal } from '../components/common';
import type { ConversationListItem, Message } from '../types/api';
import styles from './Page.module.css';

export function Conversations() {
  const [selectedAgentId, setSelectedAgentId] = useState<string | undefined>();
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);

  const { data: agents } = useAgents();
  const { data: conversations, isLoading } = useConversations(selectedAgentId);
  const { data: selectedConv, isLoading: convLoading } = useConversation(selectedConvId || '');
  const deleteConversation = useDeleteConversation();

  const agentOptions = [
    { value: '', label: 'All Agents' },
    ...(agents?.map((a) => ({ value: a.id, label: a.name || a.id.slice(0, 8) })) ?? []),
  ];

  const handleDelete = async (conv: ConversationListItem) => {
    if (confirm('Delete this conversation?')) {
      await deleteConversation.mutateAsync(conv.id);
    }
  };

  const columns = [
    {
      key: 'id',
      header: 'ID',
      render: (c: ConversationListItem) => c.id.slice(0, 8) + '...',
    },
    {
      key: 'agent_id',
      header: 'Agent',
      render: (c: ConversationListItem) => {
        const agent = agents?.find((a) => a.id === c.agent_id);
        return agent?.name || c.agent_id.slice(0, 8);
      },
    },
    { key: 'message_count', header: 'Messages', width: '100px' },
    {
      key: 'started_at',
      header: 'Started',
      render: (c: ConversationListItem) =>
        new Date(c.started_at).toLocaleString(),
    },
    {
      key: 'status',
      header: 'Status',
      width: '100px',
      render: (c: ConversationListItem) => (
        <Badge variant={c.ended_at ? 'default' : 'success'}>
          {c.ended_at ? 'ended' : 'active'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      width: '150px',
      render: (c: ConversationListItem) => (
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button variant="ghost" size="sm" onClick={() => setSelectedConvId(c.id)}>
            view
          </Button>
          <Button variant="danger" size="sm" onClick={() => handleDelete(c)}>
            delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>CONVERSATIONS</h1>
        <Select
          options={agentOptions}
          value={selectedAgentId || ''}
          onChange={(e) => setSelectedAgentId(e.target.value || undefined)}
        />
      </header>

      <div className={styles.content}>
        {isLoading ? (
          <div className={styles.loading}>
            <Spinner size="lg" />
          </div>
        ) : (
          <Table
            columns={columns}
            data={conversations || []}
            keyExtractor={(c) => c.id}
            emptyMessage="No conversations yet."
          />
        )}
      </div>

      <Modal
        isOpen={!!selectedConvId}
        onClose={() => setSelectedConvId(null)}
        title="Conversation Details"
      >
        {convLoading ? (
          <Spinner />
        ) : selectedConv ? (
          <div className={styles.conversationDetail}>
            <p>
              <strong>ID:</strong> {selectedConv.id}
            </p>
            <p>
              <strong>Messages:</strong> {selectedConv.messages.length}
            </p>
            <div className={styles.messagesList}>
              {selectedConv.messages.map((msg: Message) => (
                <div
                  key={msg.id}
                  className={`${styles.messageItem} ${styles[msg.role]}`}
                >
                  <span className={styles.messageRole}>{msg.role}:</span>
                  <span className={styles.messageText}>{msg.content}</span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
