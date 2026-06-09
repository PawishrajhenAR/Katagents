import {
  CheckCircle2,
  Search,
  Send,
  Sparkles,
  Timer,
  Users,
  type LucideIcon,
} from "lucide-react";

export interface AgentStepMeta {
  id: string;
  label: string;
  shortLabel: string;
  description: string;
  icon: LucideIcon;
}

export const EMAIL_OUTREACH_STEPS: AgentStepMeta[] = [
  {
    id: "lead_manager",
    label: "Prepare leads",
    shortLabel: "Leads",
    description: "Validates your list and marks who is ready for outreach.",
    icon: Users,
  },
  {
    id: "research",
    label: "Research prospects",
    shortLabel: "Research",
    description: "Builds a quick summary about each person and company.",
    icon: Search,
  },
  {
    id: "generate",
    label: "Write emails",
    shortLabel: "Draft",
    description: "AI writes a personalized subject and body for each lead.",
    icon: Sparkles,
  },
  {
    id: "approval",
    label: "Wait for you",
    shortLabel: "Review",
    description: "Pauses so you can approve emails before anything sends.",
    icon: CheckCircle2,
  },
  {
    id: "send",
    label: "Send emails",
    shortLabel: "Send",
    description: "Delivers only the emails you approved.",
    icon: Send,
  },
  {
    id: "follow_up",
    label: "Schedule follow-ups",
    shortLabel: "Follow-up",
    description: "Plans gentle reminders for people who did not reply.",
    icon: Timer,
  },
];

export const WORKFLOW_STEPS = [
  {
    step: 1,
    title: "Create a campaign",
    hint: "Name it and pick a tone — takes 30 seconds.",
  },
  {
    step: 2,
    title: "Add your leads",
    hint: "Import a CSV or add one test contact.",
  },
  {
    step: 3,
    title: "Run the agent",
    hint: "AI researches, writes, and queues drafts for you.",
  },
  {
    step: 4,
    title: "Approve & send",
    hint: "Review drafts, approve the good ones, agent sends them.",
  },
] as const;

export function getStepMeta(stepId: string | null | undefined): AgentStepMeta | undefined {
  return EMAIL_OUTREACH_STEPS.find((s) => s.id === stepId);
}

export function formatRunStatus(status: string): string {
  return status.replace(/_/g, " ");
}

export const RUN_STATUS_STYLES: Record<string, string> = {
  queued: "bg-slate-100 text-slate-700",
  running: "bg-teal-50 text-teal-700 agent-status-pulse",
  waiting_approval: "bg-amber-50 text-amber-800",
  completed: "bg-emerald-50 text-emerald-700",
  failed: "bg-red-50 text-red-700",
  paused: "bg-slate-100 text-slate-600",
  cancelled: "bg-slate-100 text-slate-500",
};
