from agents.base import AgentContext, StepResult


async def run_approval_gate(ctx: AgentContext) -> StepResult:
    require_approval = ctx.config.get("require_approval", True)
    if not require_approval:
        return StepResult(success=True, output={"approval_skipped": True})

    pending = await ctx.services.approval.count_pending_drafts(ctx.campaign_id, ctx.run_id)
    if pending > 0:
        ctx.log("info", f"Waiting for approval on {pending} drafts")
        return StepResult(
            success=True,
            pause=True,
            pause_reason=f"{pending} drafts pending approval",
            output={"pending_approvals": pending},
        )

    return StepResult(success=True, output={"pending_approvals": 0})
