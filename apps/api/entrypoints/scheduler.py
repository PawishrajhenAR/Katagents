"""Scheduler entrypoint — ARQ handles delayed jobs via _defer_by."""

if __name__ == "__main__":
    print("Scheduler: delayed jobs are handled by ARQ worker (_defer_by). No separate process needed.")
