// API Types for RL Chatbot

// Agents
export interface Agent {
  id: string;
  name: string | null;
  agent_type: string;
  model: string;
  temperature: number;
  system_prompt: string | null;
  config_json: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface AgentCreate {
  name?: string;
  agent_type?: string;
  model?: string;
  temperature?: number;
  system_prompt?: string;
  config_json?: Record<string, unknown>;
}

export interface AgentUpdate {
  name?: string;
  temperature?: number;
  system_prompt?: string;
  config_json?: Record<string, unknown>;
  is_active?: boolean;
}

// Chat
export interface ChatRequest {
  agent_id: string;
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  conversation_id: string;
  agent_id: string;
  message_id: string;
  response: string;
  tool_calls: ToolCall[];
  sequence_num: number;
}

export interface ToolCall {
  id: string;
  tool_name: string;
  arguments_json: Record<string, unknown> | null;
  result: string | null;
  duration_ms: number | null;
  created_at: string;
}

// Conversations
export interface Conversation {
  id: string;
  agent_id: string;
  started_at: string;
  ended_at: string | null;
  metadata_json: Record<string, unknown> | null;
  messages: Message[];
}

export interface ConversationListItem {
  id: string;
  agent_id: string;
  started_at: string;
  ended_at: string | null;
  message_count: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sequence_num: number;
  created_at: string;
  tool_calls: ToolCall[];
}

// Test Cases
export interface TestCase {
  id: string;
  name: string | null;
  user_input: string;
  expected_output: string | null;
  expected_tools_json: string[] | null;
  task_type: string;
  is_active: boolean;
  created_at: string;
}

export interface TestCaseCreate {
  name?: string;
  user_input: string;
  expected_output?: string;
  expected_tools_json?: string[];
  task_type?: string;
  is_active?: boolean;
}

export interface TestCaseUpdate {
  name?: string;
  user_input?: string;
  expected_output?: string;
  expected_tools_json?: string[];
  task_type?: string;
  is_active?: boolean;
}

// Evaluations
export interface EvaluationRun {
  id: string;
  agent_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  num_test_cases: number;
  started_at: string;
  completed_at: string | null;
  aggregate_metrics_json: Record<string, number> | null;
  results: EvaluationResult[];
}

export interface EvaluationRunListItem {
  id: string;
  agent_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  num_test_cases: number;
  started_at: string;
  completed_at: string | null;
  aggregate_metrics_json: Record<string, number> | null;
}

export interface EvaluationResult {
  id: string;
  test_case_id: string;
  task_success: number;
  tool_usage_efficiency: number;
  response_quality: number;
  reward: number;
  response_text: string | null;
  tool_calls_json: Record<string, unknown>[] | null;
}

export interface EvaluationRequest {
  agent_id: string;
  test_case_ids?: string[];
}

export interface EvaluationProgress {
  run_id: string;
  status: string;
  current_test_case: number;
  total_test_cases: number;
  progress_percent: number;
  message?: string;
}

// Training
export interface TrainingRun {
  id: string;
  agent_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  num_episodes: number;
  current_episode: number;
  final_avg_reward: number | null;
  config_json: Record<string, unknown> | null;
  started_at: string;
  completed_at: string | null;
  episodes: TrainingEpisode[];
}

export interface TrainingRunListItem {
  id: string;
  agent_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  num_episodes: number;
  current_episode: number;
  final_avg_reward: number | null;
  started_at: string;
  completed_at: string | null;
}

export interface TrainingEpisode {
  id: string;
  episode_num: number;
  avg_reward: number;
  total_reward: number;
  num_test_cases: number;
  created_at: string;
}

export interface TrainingRequest {
  agent_id: string;
  num_episodes?: number;
  test_case_ids?: string[];
  reward_weights?: Record<string, number>;
}

export interface TrainingProgress {
  run_id: string;
  status: string;
  current_episode: number;
  total_episodes: number;
  progress_percent: number;
  current_avg_reward?: number;
  message?: string;
}

// Tools
export interface Tool {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

// Health
export interface HealthResponse {
  status: string;
  service: string;
}
