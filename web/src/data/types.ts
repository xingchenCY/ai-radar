export type Article = {
  article_id: string;
  identity_keys: string[];
  source_id: string;
  publisher_id: string;
  source_name: string;
  language: string;
  title: string;
  summary_text: string;
  url: string;
  published_at: string | null;
  published_at_raw: string | null;
  date_status: string;
  date_confidence: number;
  first_seen_at: string;
  last_seen_at: string;
  content_status: string;
  relevance_score: number;
  matched_terms: string[];
  date_history: Array<{ value: string; confidence: number; observed_at: string }>;
  filter_version: string;
};

export type SourceState = {
  source_id: string;
  publisher_id?: string;
  status: string;
  attempts: number;
  http_status?: number | null;
  entry_count: number;
  accepted_count: number;
  rejected_count: number;
  error?: string | null;
  consecutive_failures: number;
  attention_required: boolean;
  last_success_at?: string | null;
};

export type Snapshot = {
  schema_version: number;
  state_version: string;
  generated_at: string;
  timezone: string;
  last_success_at: string | null;
  last_attempt_at: string;
  overall_status: string;
  articles: Article[];
  source_states: SourceState[];
  recent_runs: Array<{ at: string; overall_status: string }>;
  stats: { article_count: number; new_count: number; updated_count: number; rejected_count: number };
};
