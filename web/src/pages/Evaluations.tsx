import { useState } from 'react';
import { useEvaluations, useEvaluation, useStartEvaluation } from '../hooks/useEvaluations';
import { useAgents } from '../hooks/useAgents';
import { useTestCases } from '../hooks/useTestCases';
import { Button, Table, Badge, Modal, Select, Spinner } from '../components/common';
import type { EvaluationRunListItem } from '../types/api';
import styles from './Page.module.css';

export function Evaluations() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [detailRunId, setDetailRunId] = useState<string | null>(null);

  const { data: agents } = useAgents();
  const { data: testCases } = useTestCases();
  const { data: evaluations, isLoading } = useEvaluations();
  const { data: detailRun, isLoading: detailLoading } = useEvaluation(detailRunId || '');
  const startEvaluation = useStartEvaluation();

  const agentOptions = agents?.map((a) => ({ value: a.id, label: a.name || a.id.slice(0, 8) })) ?? [];

  const handleStart = async () => {
    if (!selectedAgentId) return;
    try {
      await startEvaluation.mutateAsync({ agent_id: selectedAgentId });
      setIsModalOpen(false);
      setSelectedAgentId('');
    } catch (e) {
      console.error('Failed to start evaluation:', e);
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'info';
      default: return 'default';
    }
  };

  const columns = [
    {
      key: 'id',
      header: 'ID',
      render: (e: EvaluationRunListItem) => e.id.slice(0, 8) + '...',
    },
    {
      key: 'agent_id',
      header: 'Agent',
      render: (e: EvaluationRunListItem) => {
        const agent = agents?.find((a) => a.id === e.agent_id);
        return agent?.name || e.agent_id.slice(0, 8);
      },
    },
    {
      key: 'status',
      header: 'Status',
      width: '100px',
      render: (e: EvaluationRunListItem) => (
        <Badge variant={getStatusVariant(e.status)}>{e.status}</Badge>
      ),
    },
    { key: 'num_test_cases', header: 'Tests', width: '80px' },
    {
      key: 'avg_reward',
      header: 'Avg Reward',
      width: '100px',
      render: (e: EvaluationRunListItem) =>
        e.aggregate_metrics_json?.avg_reward?.toFixed(3) ?? '-',
    },
    {
      key: 'started_at',
      header: 'Started',
      render: (e: EvaluationRunListItem) =>
        new Date(e.started_at).toLocaleString(),
    },
    {
      key: 'actions',
      header: 'Actions',
      width: '100px',
      render: (e: EvaluationRunListItem) => (
        <Button variant="ghost" size="sm" onClick={() => setDetailRunId(e.id)}>
          view
        </Button>
      ),
    },
  ];

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>EVALUATIONS</h1>
        <div className={styles.actions}>
          <Button variant="primary" onClick={() => setIsModalOpen(true)}>
            + Run Evaluation
          </Button>
        </div>
      </header>

      <div className={styles.content}>
        {isLoading ? (
          <div className={styles.loading}>
            <Spinner size="lg" />
          </div>
        ) : (
          <Table
            columns={columns}
            data={evaluations || []}
            keyExtractor={(e) => e.id}
            emptyMessage="No evaluations yet. Run one to get started."
          />
        )}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Run Evaluation"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleStart}
              disabled={!selectedAgentId || startEvaluation.isPending}
            >
              {startEvaluation.isPending ? 'Starting...' : 'Start'}
            </Button>
          </>
        }
      >
        <div className={styles.form}>
          <Select
            label="Agent"
            options={[{ value: '', label: '-- Select Agent --' }, ...agentOptions]}
            value={selectedAgentId}
            onChange={(e) => setSelectedAgentId(e.target.value)}
          />
          <p>Test cases: {testCases?.length ?? 0} active</p>
        </div>
      </Modal>

      <Modal
        isOpen={!!detailRunId}
        onClose={() => setDetailRunId(null)}
        title="Evaluation Results"
      >
        {detailLoading ? (
          <Spinner />
        ) : detailRun ? (
          <div>
            <p><strong>Status:</strong> {detailRun.status}</p>
            <p><strong>Test Cases:</strong> {detailRun.num_test_cases}</p>
            {detailRun.aggregate_metrics_json && (
              <div className={styles.metrics}>
                <h3>Metrics</h3>
                <p>Avg Reward: {detailRun.aggregate_metrics_json.avg_reward?.toFixed(3)}</p>
                <p>Task Success: {detailRun.aggregate_metrics_json.avg_task_success?.toFixed(3)}</p>
                <p>Tool Efficiency: {detailRun.aggregate_metrics_json.avg_tool_efficiency?.toFixed(3)}</p>
              </div>
            )}
            {detailRun.results.length > 0 && (
              <div className={styles.resultsList}>
                <h3>Results ({detailRun.results.length})</h3>
                {detailRun.results.map((r) => (
                  <div key={r.id} className={styles.resultItem}>
                    <span>Reward: {r.reward.toFixed(3)}</span>
                    <span>Success: {r.task_success.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
