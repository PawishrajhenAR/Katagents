EMAIL_OUTREACH_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "tone": {"type": "string"},
        "max_follow_ups": {"type": "integer"},
        "follow_up_delay_days": {"type": "integer"},
        "require_approval": {"type": "boolean"},
    },
}
