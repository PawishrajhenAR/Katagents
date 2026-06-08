import agents.email_outreach.agent  # noqa: F401 — register agent
from arq.worker import run_worker

from jobs.tasks import WorkerSettings

if __name__ == "__main__":
    run_worker(WorkerSettings)
