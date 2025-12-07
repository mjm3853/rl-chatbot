import { useAgents } from '../hooks/useAgents';
import { useConversations } from '../hooks/useConversations';
import { useTestCases } from '../hooks/useTestCases';
import { useEvaluations } from '../hooks/useEvaluations';
import { useTrainingRuns } from '../hooks/useTraining';
import { Spinner } from '../components/common';
import styles from './Page.module.css';

export function Dashboard() {
  const { data: agents, isLoading: agentsLoading } = useAgents();
  const { data: conversations, isLoading: convsLoading } = useConversations();
  const { data: testCases, isLoading: testsLoading } = useTestCases();
  const { data: evaluations, isLoading: evalsLoading } = useEvaluations();
  const { data: trainingRuns, isLoading: trainLoading } = useTrainingRuns();

  const isLoading = agentsLoading || convsLoading || testsLoading || evalsLoading || trainLoading;

  const stats = [
    { label: 'Agents', value: agents?.length ?? '-' },
    { label: 'Conversations', value: conversations?.length ?? '-' },
    { label: 'Test Cases', value: testCases?.length ?? '-' },
    { label: 'Evaluations', value: evaluations?.length ?? '-' },
    { label: 'Training Runs', value: trainingRuns?.length ?? '-' },
  ];

  const recentEvals = evaluations?.slice(0, 5) ?? [];
  const recentTraining = trainingRuns?.slice(0, 5) ?? [];

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>DASHBOARD</h1>
        {isLoading && <Spinner size="sm" />}
      </header>

      <div className={styles.content}>
        <div className={styles.statsGrid}>
          {stats.map((stat) => (
            <div key={stat.label} className={styles.statCard}>
              <h3>{stat.label}</h3>
              <div className={styles.statValue}>{stat.value}</div>
            </div>
          ))}
        </div>

        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2>Recent Evaluations</h2>
          </div>
          {recentEvals.length === 0 ? (
            <p>No evaluations yet</p>
          ) : (
            <table className={styles.miniTable}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Status</th>
                  <th>Test Cases</th>
                  <th>Started</th>
                </tr>
              </thead>
              <tbody>
                {recentEvals.map((e) => (
                  <tr key={e.id}>
                    <td>{e.id.slice(0, 8)}...</td>
                    <td>{e.status}</td>
                    <td>{e.num_test_cases}</td>
                    <td>{new Date(e.started_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2>Recent Training Runs</h2>
          </div>
          {recentTraining.length === 0 ? (
            <p>No training runs yet</p>
          ) : (
            <table className={styles.miniTable}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Status</th>
                  <th>Episodes</th>
                  <th>Avg Reward</th>
                </tr>
              </thead>
              <tbody>
                {recentTraining.map((t) => (
                  <tr key={t.id}>
                    <td>{t.id.slice(0, 8)}...</td>
                    <td>{t.status}</td>
                    <td>{t.current_episode}/{t.num_episodes}</td>
                    <td>{t.final_avg_reward?.toFixed(3) ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
