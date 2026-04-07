export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active?: boolean;
  avatar_url?: string;
}

export interface Repository {
  id: number;
  name: string;
  url: string;
  provider: string;
  branch: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_scan_at?: string;
  config?: Record<string, any>;
}

export interface Scan {
  id: number;
  repository_id: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  trigger_type: 'manual' | 'scheduled' | 'webhook';
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  files_scanned: number;
  documents_generated: number;
}

export interface Document {
  id: number;
  repository_id: number;
  scan_id?: number;
  title: string;
  slug: string;
  doc_type: 'api' | 'class' | 'function' | 'config' | 'example' | 'module';
  path?: string;
  language?: string;
  summary?: string;
  content: string;
  examples?: UsageExample[];
  embedding_id?: string;
  version?: string;
  is_latest: boolean;
  created_at: string;
  updated_at: string;
}

export interface UsageExample {
  code: string;
  file_path: string;
  line_number: number;
  context?: string;
  is_redacted: boolean;
}

export interface SearchResult {
  id: number;
  score: number;
  snippet: string;
  repository_name: string;
  title: string;
  slug: string;
  doc_type: string;
  path?: string;
  language?: string;
  summary?: string;
  file_path?: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
  took_ms: number;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
