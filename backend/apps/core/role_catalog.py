"""
كتالوج الأدوار — نموذج مبسّط (3 أدوار نشطة).
"""
from __future__ import annotations

import re

from apps.core.models import Role
from apps.core.workflow_simple import ACTIVE_ROLE_TYPES


def role_type_label(role_type: str) -> str:
    entry = ROLE_CATALOG.get(role_type)
    if entry:
        return entry['type_label']
    return role_type


def role_type_choices() -> list[tuple[str, str]]:
    return [(code, ROLE_CATALOG[code]['type_label']) for code in ROLE_TYPE_ORDER]


ROLE_TYPE_ORDER = [
    Role.RoleType.ADMIN,
    Role.RoleType.HR_MANAGER,
    Role.RoleType.SPECIALIST,
]

ROLE_CATALOG: dict[str, dict[str, str]] = {
    Role.RoleType.ADMIN: {
        'code': 'ADMIN',
        'name': 'ADMIN — مدير النظام',
        'type_label': 'ADMIN — مدير النظام (صلاحيات كاملة)',
        'description': 'صلاحيات كاملة: مستخدمون، إعدادات، موظفون، رواتب، تقارير، واعتماد الطلبات.',
    },
    Role.RoleType.HR_MANAGER: {
        'code': 'HR_MANAGER',
        'name': 'HR_MANAGER — مدير الموارد',
        'type_label': 'HR_MANAGER — مدير الموارد (اعتماد وتنفيذ)',
        'description': (
            'اعتماد طلبات مدخل الموارد وتنفيذها، إدارة الموظفين والرواتب والتقارير على مستوى الشركة.'
        ),
    },
    Role.RoleType.SPECIALIST: {
        'code': 'HR_ENTRY',
        'name': 'HR_ENTRY — مدخل الموارد',
        'type_label': 'HR_ENTRY — مدخل الموارد (إدخال ورفع الطلبات)',
        'description': (
            'إدخال وتحديث بيانات الموظفين ورفع طلبات العمليات السريعة — يرى كل الفروع.'
        ),
    },
}

LEGACY_ROLE_NAME_TO_TYPE: dict[str, str] = {
    'الأدمن': Role.RoleType.ADMIN,
    'مدير النظام': Role.RoleType.ADMIN,
    'مدير الموارد البشرية': Role.RoleType.HR_MANAGER,
    'مدير الموارد': Role.RoleType.HR_MANAGER,
    'الموارد البشرية': Role.RoleType.HR_MANAGER,
    'أخصائي موارد بشرية': Role.RoleType.SPECIALIST,
    'أخصائي إدخال البيانات': Role.RoleType.SPECIALIST,
    'مدخل الموارد': Role.RoleType.SPECIALIST,
    'مدير إدارة': Role.RoleType.HR_MANAGER,
    'مدير فرع': Role.RoleType.HR_MANAGER,
    'محاسب الفرع': Role.RoleType.HR_MANAGER,
    'موظف': Role.RoleType.SPECIALIST,
    'مدير المالية': Role.RoleType.HR_MANAGER,
    'المدير التقني': Role.RoleType.ADMIN,
    'منفّذ الموارد البشرية': Role.RoleType.SPECIALIST,
}


def _extract_arabic_label(text: str) -> str:
    label = (text or '').strip()
    if not label:
        return '—'
    if ' — ' in label:
        label = label.split(' — ', 1)[1].strip()
    label = re.sub(r'\s*\([^)]*\)\s*$', '', label).strip()
    return label or '—'


def arabic_role_label(*, role_type: str | None = None, name: str | None = None) -> str:
    if role_type and role_type in ROLE_CATALOG:
        return _extract_arabic_label(ROLE_CATALOG[role_type]['name'])
    if name:
        return _extract_arabic_label(name)
    return '—'


def is_active_role_type(role_type: str) -> bool:
    return role_type in ACTIVE_ROLE_TYPES
