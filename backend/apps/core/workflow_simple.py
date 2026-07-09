"""
نموذج تشغيل مبسّط — HR_SEED
============================
• 3 أدوار فقط: أدمن، مدير موارد، مدخل موارد
• اعتماد واحد: مدخل يرفع → مدير الموارد يعتمد ويُنفّذ
• بدون تقييد بالفروع/الإدارات لمدخل ومدير الموارد
"""
from __future__ import annotations

from apps.core.models import Role

ACTIVE_ROLE_TYPES = frozenset({
    Role.RoleType.ADMIN,
    Role.RoleType.HR_MANAGER,
    Role.RoleType.SPECIALIST,
})

# أدوار قديمة → الدور الجديد عند الترحيل
LEGACY_ROLE_MIGRATION_MAP: dict[str, str] = {
    Role.RoleType.HR_OFFICER: Role.RoleType.SPECIALIST,
    Role.RoleType.ADMIN_MANAGER: Role.RoleType.HR_MANAGER,
    Role.RoleType.MANAGER: Role.RoleType.HR_MANAGER,
    Role.RoleType.BRANCH_ACCOUNTANT: Role.RoleType.HR_MANAGER,
    Role.RoleType.EMPLOYEE: Role.RoleType.SPECIALIST,
    Role.RoleType.MAINTENANCE_MANAGER: Role.RoleType.HR_MANAGER,
}

COMPANY_WIDE_ROLE_TYPES = frozenset({
    Role.RoleType.ADMIN,
    Role.RoleType.HR_MANAGER,
    Role.RoleType.SPECIALIST,
})


def is_simple_hr_entry(user) -> bool:
    rt = _role_type(user)
    return rt == Role.RoleType.SPECIALIST


def is_simple_hr_manager(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    rt = _role_type(user)
    return rt in {Role.RoleType.ADMIN, Role.RoleType.HR_MANAGER}


def _role_type(user) -> str | None:
    profile = getattr(user, 'profile', None)
    role = profile.role if profile else None
    return role.role_type if role else None
