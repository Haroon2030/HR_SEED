"""توجيه الاعتماد — نموذج مبسّط: موظف الموارد يرفع → المدير يعتمِد."""
from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Q

from apps.core.models import Notification


class FirstApproverKind:
    HR_MANAGER = 'hr_manager'
    NONE = 'none'


@dataclass(frozen=True)
class FirstApproverDecision:
    kind: str
    recipient: object | None
    administration: object | None = None
    branch: object | None = None

    @property
    def stage_label(self) -> str:
        if self.recipient:
            return approver_display_label(self.recipient)
        return 'مدير الموارد'


def _profile_and_role(user):
    from apps.core.models import UserProfile

    profile = (
        UserProfile.objects.filter(user_id=user.pk)
        .select_related('role')
        .first()
    )
    return profile, (profile.role if profile else None)


def approver_display_label(user) -> str:
    from apps.core.role_catalog import arabic_role_label

    if not user:
        return 'غير محدد'
    _profile, role = _profile_and_role(user)
    if role:
        label = arabic_role_label(role_type=role.role_type, name=getattr(role, 'name', None))
        if label and label != '—':
            return label
    full = user.get_full_name() if hasattr(user, 'get_full_name') else ''
    return (full or getattr(user, 'username', '') or 'غير محدد').strip()


def first_stage_tab_label(user) -> str:
    return 'تعميد المدير'


def snapshot_routing_fields(employee) -> dict:
    return {
        'branch': getattr(employee, 'branch', None),
        'administration': getattr(employee, 'administration', None),
    }


def resolve_first_approver(obj) -> FirstApproverDecision:
    return FirstApproverDecision(
        kind=FirstApproverKind.HR_MANAGER,
        recipient=None,
        branch=getattr(obj, 'branch', None),
        administration=getattr(obj, 'administration', None),
    )


def user_can_first_approve(user, obj) -> bool:
    from apps.core.workflow_simple import is_simple_hr_manager
    return is_simple_hr_manager(user)


def first_stage_pending_q(user, *, model_status_pending_branch: str) -> Q:
    """لا توجد مرحلة فرع/إدارة — الطلبات تبدأ مباشرة عند مدير الموارد."""
    return Q(pk__in=[])


def notify_on_first_stage(
    obj,
    *,
    title: str,
    message: str = '',
    icon: str = 'inbox',
    color: str = Notification.Color.PRIMARY,
):
    """إشعار مديري الموارد عند إنشاء أو إعادة إرسال طلب."""
    from apps.core.services import notifications as notif
    from apps.core.services.whatsapp import workflow_notifier
    from apps.employees.models import EmploymentRequest

    workflow_notifier.notify_whatsapp_request_created(obj)

    if isinstance(obj, EmploymentRequest):
        from apps.core.services.employment_requests import _notify_general_managers

        _notify_general_managers(obj, title=title, message=message, icon=icon, color=color)
        return

    notif.notify_general_managers(
        obj,
        title=title,
        message=message,
        icon=icon,
        color=color,
    )
