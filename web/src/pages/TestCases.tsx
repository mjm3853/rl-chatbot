import { useState } from 'react';
import { useTestCases, useCreateTestCase, useDeleteTestCase } from '../hooks/useTestCases';
import { Button, Table, Badge, Modal, Input, Spinner } from '../components/common';
import type { TestCase, TestCaseCreate } from '../types/api';
import styles from './Page.module.css';

export function TestCases() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState<TestCaseCreate>({
    name: '',
    user_input: '',
    expected_output: '',
    expected_tools_json: [],
    task_type: 'contains',
  });

  const { data: testCases, isLoading, error } = useTestCases();
  const createTestCase = useCreateTestCase();
  const deleteTestCase = useDeleteTestCase();

  const handleCreate = async () => {
    try {
      await createTestCase.mutateAsync(formData);
      setIsModalOpen(false);
      setFormData({
        name: '',
        user_input: '',
        expected_output: '',
        expected_tools_json: [],
        task_type: 'contains',
      });
    } catch (e) {
      console.error('Failed to create test case:', e);
    }
  };

  const handleDelete = async (tc: TestCase) => {
    if (confirm(`Delete test case "${tc.name || tc.id}"?`)) {
      try {
        await deleteTestCase.mutateAsync(tc.id);
      } catch (e) {
        console.error('Failed to delete test case:', e);
      }
    }
  };

  const columns = [
    { key: 'name', header: 'Name', render: (tc: TestCase) => tc.name || '-' },
    {
      key: 'user_input',
      header: 'Input',
      render: (tc: TestCase) =>
        tc.user_input.length > 50
          ? tc.user_input.slice(0, 50) + '...'
          : tc.user_input,
    },
    { key: 'task_type', header: 'Type', width: '100px' },
    {
      key: 'expected_tools',
      header: 'Tools',
      render: (tc: TestCase) =>
        tc.expected_tools_json?.join(', ') || '-',
    },
    {
      key: 'is_active',
      header: 'Status',
      width: '100px',
      render: (tc: TestCase) => (
        <Badge variant={tc.is_active ? 'success' : 'default'}>
          {tc.is_active ? 'active' : 'inactive'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      width: '100px',
      render: (tc: TestCase) => (
        <Button variant="danger" size="sm" onClick={() => handleDelete(tc)}>
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
        <div className={styles.error}>Failed to load test cases</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>TEST CASES</h1>
        <div className={styles.actions}>
          <Button variant="primary" onClick={() => setIsModalOpen(true)}>
            + New Test Case
          </Button>
        </div>
      </header>

      <div className={styles.content}>
        <Table
          columns={columns}
          data={testCases || []}
          keyExtractor={(tc) => tc.id}
          emptyMessage="No test cases yet. Create one to get started."
        />
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Test Case"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleCreate}
              disabled={!formData.user_input || createTestCase.isPending}
            >
              {createTestCase.isPending ? 'Creating...' : 'Create'}
            </Button>
          </>
        }
      >
        <div className={styles.form}>
          <Input
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Test case name"
          />
          <Input
            label="User Input"
            value={formData.user_input}
            onChange={(e) => setFormData({ ...formData, user_input: e.target.value })}
            placeholder="What is 2 + 2?"
          />
          <Input
            label="Expected Output"
            value={formData.expected_output}
            onChange={(e) => setFormData({ ...formData, expected_output: e.target.value })}
            placeholder="4"
          />
          <Input
            label="Expected Tools (comma-separated)"
            value={formData.expected_tools_json?.join(', ')}
            onChange={(e) =>
              setFormData({
                ...formData,
                expected_tools_json: e.target.value
                  .split(',')
                  .map((s) => s.trim())
                  .filter(Boolean),
              })
            }
            placeholder="calculate, search"
          />
        </div>
      </Modal>
    </div>
  );
}
