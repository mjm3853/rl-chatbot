import { useState } from 'react';
import { useTrainingRuns, useTrainingRun, useStartTraining, useStopTraining } from '../hooks/useTraining';
import { useAgents } from '../hooks/useAgents';
import { Button, Table, Badge, Modal, Select, Input, Spinner, ProgressBar } from '../components/common';
import type { TrainingRunListItem } from '../types/api';
import styles from './Page.module.css';

export function Training() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [numEpisodes, setNumEpisodes] = useState(10);
  const [detailRunId, setDetailRunId] = useState<string | null>(null);

  const { data: agents } = useAgents();
  const { data: trainingRuns, isLoading } = useTrainingRuns();
  const { data: detailRun, isLoading: detailLoading } = useTrainingRun(detailRunId || '');
  const startTraining = useStartTraining();
  const stopTraining = useStopTraining();

  const agentOptions = agents?.map((a) => ({ value: a.id, label: a.name || a.id.slice(0, 8) })) ?? [];

  const handleStart = async () => {
    if (!selectedAgentId) return;
    try {
      await startTraining.mutateAsync({
        agent_id: selectedAgentId,
        num_episodes: numEpisodes,
      });
      setIsModalOpen(false);
      setSelectedAgentId('');
    } catch (e) {
      console.error('Failed to start training:', e);
    }
  };

  const handleStop = async (run: TrainingRunListItem) => {
    if (confirm('Stop this training run?')) {
      try {
        await stopTraining.mutateAsync(run.id);
      } catch (e) {
        console.error('Failed to stop training:', e);
      }
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      case 'running': return 'info';
      default: return 'default';
    }
  };

  const columns = [
    {
      key: 'id',
      header: 'ID',
      render: (t: TrainingRunListItem) => t.id.slice(0, 8) + '...',
    },
    {
      key: 'agent_id',
      header: 'Agent',
      render: (t: TrainingRunListItem) => {
        const agent = agents?.find((a) => a.id === t.agent_id);
        return agent?.name || t.agent_id.slice(0, 8);
      },
    },
    {
      key: 'status',
      header: 'Status',
      width: '100px',
      render: (t: TrainingRunListItem) => (
        <Badge variant={getStatusVariant(t.status)}>{t.status}</Badge>
      ),
    },
    {
      key: 'progress',
      header: 'Progress',
      width: '150px',
      render: (t: TrainingRunListItem) => (
        <span>{t.current_episode}/{t.num_episodes}</span>
      ),
    },
    {
      key: 'avg_reward',
      header: 'Avg Reward',
      width: '100px',
      render: (t: TrainingRunListItem) => t.final_avg_reward?.toFixed(3) ?? '-',
    },
    {
      key: 'started_at',
      header: 'Started',
      render: (t: TrainingRunListItem) =>
        new Date(t.started_at).toLocaleString(),
    },
    {
      key: 'actions',
      header: 'Actions',
      width: '150px',
      render: (t: TrainingRunListItem) => (
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button variant="ghost" size="sm" onClick={() => setDetailRunId(t.id)}>
            view
          </Button>
          {t.status === 'running' && (
            <Button variant="danger" size="sm" onClick={() => handleStop(t)}>
              stop
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>TRAINING</h1>
        <div className={styles.actions}>
          <Button variant="primary" onClick={() => setIsModalOpen(true)}>
            + Start Training
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
            data={trainingRuns || []}
            keyExtractor={(t) => t.id}
            emptyMessage="No training runs yet. Start one to get started."
          />
        )}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Start Training"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleStart}
              disabled={!selectedAgentId || startTraining.isPending}
            >
              {startTraining.isPending ? 'Starting...' : 'Start'}
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
          <Input
            label="Number of Episodes"
            type="number"
            min={1}
            max={100}
            value={numEpisodes}
            onChange={(e) => setNumEpisodes(parseInt(e.target.value) || 10)}
          />
        </div>
      </Modal>

      <Modal
        isOpen={!!detailRunId}
        onClose={() => setDetailRunId(null)}
        title="Training Run Details"
      >
        {detailLoading ? (
          <Spinner />
        ) : detailRun ? (
          <div>
            <p><strong>Status:</strong> {detailRun.status}</p>
            <p><strong>Episodes:</strong> {detailRun.current_episode}/{detailRun.num_episodes}</p>
            <ProgressBar
              value={detailRun.current_episode}
              max={detailRun.num_episodes}
              label="Progress"
            />
            {detailRun.final_avg_reward !== null && (
              <p><strong>Final Avg Reward:</strong> {detailRun.final_avg_reward.toFixed(3)}</p>
            )}
            {detailRun.episodes.length > 0 && (
              <div className={styles.episodesList}>
                <h3>Episodes</h3>
                {detailRun.episodes.map((ep) => (
                  <div key={ep.id} className={styles.episodeItem}>
                    <span>#{ep.episode_num}</span>
                    <span>Avg: {ep.avg_reward.toFixed(3)}</span>
                    <span>Total: {ep.total_reward.toFixed(3)}</span>
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
