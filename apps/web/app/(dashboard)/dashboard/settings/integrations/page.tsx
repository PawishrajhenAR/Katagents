import { Card } from "@/components/ui/input";
import { PageHeader } from "@/components/layout/page-header";

export default function IntegrationsPage() {
  return (
    <div className="w-full min-w-0 space-y-6 animate-fade-up">
      <PageHeader
        title="Integrations"
        description="Set these in apps/api/.env, then restart the API."
      />

      <Card>
        <p className="font-display font-semibold">Resend (Email)</p>
        <p className="mt-2 text-sm text-muted">
          Without <code className="rounded bg-background px-1">RESEND_API_KEY</code>, emails are mock-sent locally — safe for testing.
        </p>
        <pre className="mt-4 overflow-x-auto rounded-lg bg-background p-3 text-xs">
{`RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=you@yourdomain.com`}
        </pre>
      </Card>

      <Card>
        <p className="font-display font-semibold">AI (Gemini)</p>
        <p className="mt-2 text-sm text-muted">
          Without a key, the agent uses mock research and email copy — enough to test the full flow.
        </p>
        <pre className="mt-4 overflow-x-auto rounded-lg bg-background p-3 text-xs">
{`GEMINI_API_KEY=...
LLM_PROVIDER=gemini`}
        </pre>
      </Card>
    </div>
  );
}
