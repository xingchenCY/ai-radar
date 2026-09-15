import type { Snapshot } from './types';

const raw = {
  schema_version: 1,
  state_version: 'bootstrap',
  generated_at: '2026-09-14T15:47:35Z',
  timezone: 'Asia/Shanghai',
  last_success_at: null,
  last_attempt_at: '2026-09-14T15:47:35Z',
  overall_status: 'degraded',
  articles: [],
  source_states: [],
  recent_runs: [],
  stats: { article_count: 0, new_count: 0, updated_count: 0, rejected_count: 0 },
} satisfies Snapshot;

export default raw;
