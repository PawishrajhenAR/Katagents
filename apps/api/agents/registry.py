from dataclasses import dataclass
from typing import Type

_REGISTRY: dict[str, "RegisteredAgent"] = {}


@dataclass
class RegisteredAgent:
    agent_type: str
    agent_class: Type
    display_name: str
    description: str
    version: str
    required_integrations: list[str]


def register_agent(
    agent_type: str,
    *,
    display_name: str,
    description: str = "",
    version: str = "1.0.0",
    required_integrations: list[str] | None = None,
):
    def decorator(cls):
        _REGISTRY[agent_type] = RegisteredAgent(
            agent_type=agent_type,
            agent_class=cls,
            display_name=display_name,
            description=description,
            version=version,
            required_integrations=required_integrations or [],
        )
        return cls

    return decorator


def get_agent_class(agent_type: str) -> Type:
    if agent_type not in _REGISTRY:
        raise KeyError(f"Unknown agent type: {agent_type}")
    return _REGISTRY[agent_type].agent_class


def list_agents() -> list[RegisteredAgent]:
    return list(_REGISTRY.values())
