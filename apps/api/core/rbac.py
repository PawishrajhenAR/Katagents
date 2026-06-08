from enum import IntEnum

from models.user import OrgRole


class RoleLevel(IntEnum):
    VIEWER = 1
    REVIEWER = 2
    MANAGER = 3
    ADMIN = 4


ROLE_LEVELS: dict[str, RoleLevel] = {
    OrgRole.VIEWER.value: RoleLevel.VIEWER,
    OrgRole.REVIEWER.value: RoleLevel.REVIEWER,
    OrgRole.MANAGER.value: RoleLevel.MANAGER,
    OrgRole.ADMIN.value: RoleLevel.ADMIN,
}


def has_min_role(user_role: str, required: str) -> bool:
    return ROLE_LEVELS.get(user_role, RoleLevel.VIEWER) >= ROLE_LEVELS.get(required, RoleLevel.ADMIN)


def can_write_campaigns(role: str) -> bool:
    return has_min_role(role, OrgRole.MANAGER.value)


def can_approve_drafts(role: str) -> bool:
    return has_min_role(role, OrgRole.REVIEWER.value)


def can_manage_org(role: str) -> bool:
    return has_min_role(role, OrgRole.ADMIN.value)
