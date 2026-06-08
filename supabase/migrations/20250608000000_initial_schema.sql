-- KatalyzU Agent Platform initial schema (mirrors apps/api/migrations/versions/001_initial_schema.py)

CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    settings_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_users_email ON users (email);

CREATE TABLE organization_members (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(50) NOT NULL DEFAULT 'admin',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_org_user UNIQUE (org_id, user_id)
);

CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_refresh_tokens_token_hash ON refresh_tokens (token_hash);

CREATE TABLE campaigns (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES users(id),
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_campaigns_org_id ON campaigns (org_id);

CREATE TABLE leads (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(id),
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    company VARCHAR(255),
    title VARCHAR(255),
    source VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'imported',
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_org_lead_email UNIQUE (org_id, email)
);
CREATE INDEX ix_leads_org_id ON leads (org_id);

CREATE TABLE campaign_leads (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    lead_id UUID NOT NULL REFERENCES leads(id),
    status VARCHAR(50) NOT NULL DEFAULT 'imported',
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_campaign_lead UNIQUE (campaign_id, lead_id)
);

CREATE TABLE lead_imports (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    file_url TEXT,
    row_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_runs (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    org_id UUID NOT NULL REFERENCES organizations(id),
    agent_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    current_step VARCHAR(100),
    context_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error TEXT,
    triggered_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_agent_runs_campaign_id ON agent_runs (campaign_id);
CREATE INDEX ix_agent_runs_status ON agent_runs (status);

CREATE TABLE agent_steps (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES agent_runs(id),
    step_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    input_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    attempt INTEGER NOT NULL DEFAULT 1,
    duration_ms INTEGER,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_logs (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES agent_runs(id),
    level VARCHAR(20) NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE research_records (
    id UUID PRIMARY KEY,
    lead_id UUID NOT NULL REFERENCES leads(id),
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    agent_run_id UUID REFERENCES agent_runs(id),
    summary TEXT NOT NULL,
    sources_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE email_drafts (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    lead_id UUID NOT NULL REFERENCES leads(id),
    agent_run_id UUID REFERENCES agent_runs(id),
    subject VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_email_drafts_campaign_status ON email_drafts (campaign_id, status);

CREATE TABLE approval_items (
    id UUID PRIMARY KEY,
    draft_id UUID NOT NULL REFERENCES email_drafts(id),
    assigned_to UUID REFERENCES users(id),
    decision VARCHAR(50) NOT NULL DEFAULT 'pending',
    decided_at TIMESTAMPTZ,
    notes TEXT,
    decided_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE emails (
    id UUID PRIMARY KEY,
    draft_id UUID REFERENCES email_drafts(id),
    lead_id UUID NOT NULL REFERENCES leads(id),
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    org_id UUID NOT NULL REFERENCES organizations(id),
    resend_id VARCHAR(255) UNIQUE,
    subject VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    to_email VARCHAR(255) NOT NULL,
    sent_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE email_replies (
    id UUID PRIMARY KEY,
    email_id UUID NOT NULL REFERENCES emails(id),
    from_address VARCHAR(255) NOT NULL,
    body_text TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    classification VARCHAR(50),
    classification_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    resend_event_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE email_events (
    id UUID PRIMARY KEY,
    email_id UUID NOT NULL REFERENCES emails(id),
    event_type VARCHAR(50) NOT NULL,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE unsubscribes (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(id),
    email VARCHAR(255) NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_org_unsubscribe UNIQUE (org_id, email)
);

CREATE TABLE analytics_events (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(id),
    event_name VARCHAR(100) NOT NULL,
    properties_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    campaign_id UUID REFERENCES campaigns(id),
    run_id UUID REFERENCES agent_runs(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_analytics_events_org_event ON analytics_events (org_id, event_name, created_at);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    ip VARCHAR(45),
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE integrations (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(id),
    provider VARCHAR(50) NOT NULL,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'inactive',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
