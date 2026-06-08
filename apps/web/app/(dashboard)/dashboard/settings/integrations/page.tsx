import { Card } from "@/components/ui/input";

export default function IntegrationsPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold">Integrations</h1>
      <Card className="mt-8">
        <p className="font-medium">Resend (Email)</p>
        <p className="mt-1 text-sm text-muted">
          Configure RESEND_API_KEY and RESEND_FROM_EMAIL in your backend environment.
        </p>
      </Card>
      <Card className="mt-4">
        <p className="font-medium">AI Providers</p>
        <p className="mt-1 text-sm text-muted">
          Set GEMINI_API_KEY or OPENAI_API_KEY in backend environment. LLM_PROVIDER controls routing.
        </p>
      </Card>
    </div>
  );
}
