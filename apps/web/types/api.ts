export interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
  settings_json: Record<string, unknown>;
}

export interface AuthMeResponse {
  user: User;
  orgs: Organization[];
  current_org: Organization | null;
  role: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Campaign {
  id: string;
  org_id: string;
  name: string;
  agent_type: string;
  status: string;
  config_json: Record<string, unknown>;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  lead_count: number;
  pending_drafts: number;
}

export interface Lead {
  id: string;
  org_id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  company: string | null;
  title: string | null;
  source: string | null;
  status: string;
  metadata_json: Record<string, unknown>;
  campaign_status: string | null;
}

export interface AgentRun {
  id: string;
  campaign_id: string;
  org_id: string;
  agent_type: string;
  status: string;
  current_step: string | null;
  context_json: Record<string, unknown>;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
  created_at: string;
}

export interface AgentStep {
  id: string;
  run_id: string;
  step_name: string;
  status: string;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown>;
  attempt: number;
  duration_ms: number | null;
  error: string | null;
  created_at: string;
}

export interface AgentLog {
  id: string;
  run_id: string;
  level: string;
  message: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export interface AgentRunDetail extends AgentRun {
  steps: AgentStep[];
}

export interface Draft {
  id: string;
  campaign_id: string;
  lead_id: string;
  agent_run_id: string | null;
  subject: string;
  body: string;
  status: string;
  version: number;
  created_at: string;
  lead_email: string | null;
  lead_name: string | null;
}

export interface Email {
  id: string;
  campaign_id: string;
  lead_id: string;
  subject: string;
  to_email: string;
  status: string;
  sent_at: string | null;
}

export interface Reply {
  id: string;
  email_id: string;
  from_address: string;
  body_text: string;
  received_at: string;
  classification: string | null;
  classification_json: Record<string, unknown>;
}

export interface AgentMetadata {
  agent_type: string;
  display_name: string;
  description: string;
  version: string;
  required_integrations: string[];
}

export interface AnalyticsOverview {
  total_campaigns: number;
  active_campaigns: number;
  total_leads: number;
  emails_sent: number;
  emails_delivered: number;
  replies_received: number;
  reply_rate: number;
  pending_approvals: number;
}

export interface LeadImportResult {
  imported: number;
  skipped: number;
  errors: string[];
  import_id: string;
}

export interface Paginated<T> {
  data: T[];
  meta?: { page: number; per_page: number; total: number };
}
