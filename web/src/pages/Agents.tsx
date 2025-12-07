import { useState } from 'react';
import { useAgents, useCreateAgent, useDeleteAgent } from '../hooks/useAgents';
import { Button, Table, Badge, Modal, Input, Select, Spinner } from '../components/common';
import type { Agent, AgentCreate } from '../types/api';
import styles from './Page.module.css';

const modelOptions = [
  { value: 'gpt-4o', label: 'gpt-4o' },
  { value: 'gpt-4o-mini', label: 'gpt-4o-mini' },
  { value: 'gpt-4-turbo', label: 'gpt-4-turbo' },
  { value: 'gpt-3.5-turbo', label: 'gpt-3.5-turbo' },
];

export function Agents() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState<AgentCreate>({
    name: '',
    model: 'gpt-4o',
    temperature: 0.7,
    agent_type: 'openai',
  });

  const { data: agents, isLoading, error } = useAgents();
  const createAgent = useCreateAgent();
  const deleteAgent = useDeleteAgent();

  const handleCreate = async () => {
    try {
      await createAgent.mutateAsync(formData);
      setIsModalOpen(false);
      setFormData({ name: '', model: 'gpt-4o', temperature: 0.7, agent_type: 'openai' });
    } catch (e) {
      console.error('Failed to create agent:', e);
    }
  };

  const handleDelete = async (agent: Agent) => {
    if (confirm(`Delete agent "${agent.name || agent.id}"?`)) {
      try {
        await deleteAgent.mutateAsync(agent.id);
      } catch (e) {
        console.error('Failed to delete agent:', e);
      }
    }
  };

  const columns = [
    { key: 'name', header: 'Name', render: (a: Agent) => a.name || '-' },
    { key: 'model', header: 'Model' },
    { key: 'temperature', header: 'Temp', width: '80px' },
    { key: 'agent_type', header: 'Type' },
    {
      key: 'is_active',
      header: 'Status',
      width: '100px',
      render: (a: Agent) => (
        <Badge variant={a.is_active ? 'success' : 'default'}>
          {a.is_active ? 'active' : 'inactive'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      width: '100px',
      render: (a: Agent) => (
        <Button variant="danger" size="sm" onClick={() => handleDelete(a)}>
          delete
        </Button>
      ),
    },
  ];

  if (isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.loading}>
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.error}>Failed to load agents: {(error as Error).message}</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>AGENTS</h1>
        <div className={styles.actions}>
          <Button variant="primary" onClick={() => setIsModalOpen(true)}>
            + New Agent
          </Button>
        </div>
      </header>

      <div className={styles.content}>
        <Table
          columns={columns}
          data={agents || []}
          keyExtractor={(a) => a.id}
          emptyMessage="No agents yet. Create one to get started."
        />
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Agent"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleCreate}
              disabled={createAgent.isPending}
            >
              {createAgent.isPending ? 'Creating...' : 'Create'}
            </Button>
          </>
        }
      >
        <div className={styles.form}>
          <Input
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="My Agent"
          />
          <Select
            label="Model"
            options={modelOptions}
            value={formData.model}
            onChange={(e) => setFormData({ ...formData, model: e.target.value })}
          />
          <Input
            label="Temperature"
            type="number"
            min={0}
            max={2}
            step={0.1}
            value={formData.temperature}
            onChange={(e) =>
              setFormData({ ...formData, temperature: parseFloat(e.target.value) })
            }
          />
        </div>
      </Modal>
    </div>
  );
}
