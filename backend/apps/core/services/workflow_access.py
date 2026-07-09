"""
صلاحيات دورة الموافقات (طلبات العمليات + التوظيف).
تُدمج مع فحص الأدوار/الفروع في _helpers._can_act_at_stage.
"""
from __future__ import annotations

from apps.core.decorators import has_permission, _is_super_or_admin
from apps.core.models import PendingAction

STAGE_PERMISSION = {
    PendingAction.Stage.BRANCH: 'operations.approve_branch',
    PendingAction.Stage.GM: 'operations.approve_gm',
    PendingAction.Stage.OFFICER: 'operations.approve_officer',
}

RETURN_PERMISSION = 'operations.return'
RESUBMIT_PERMISSION = 'operations.resubmit'
VIEW_PERMISSION = 'operations.view'

WORKFLOW_PERMISSION_CODES = (
    VIEW_PERMISSION,
    'operations.approve_branch',
    'operations.approve_admin',
    'operations.approve_gm',
    'operations.approve_officer',
    RETURN_PERMISSION,
    RESUBMIT_PERMISSION,
)

from apps.core.permissions_registry import register_module, register_permission

register_module('operations', name='طلبات العمليات', icon='list-checks', order=12)
for _code in WORKFLOW_PERMISSION_CODES:
    register_permission(_code)


def can_view_operations(user) -> bool:
    """عرض قائمة/تفاصيل طلبات العمليات — صلاحيات DB فقط (بدون تجاوز بالدور الوظيفي)."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or _is_super_or_admin(user):
        return True
    if has_permission(user, VIEW_PERMISSION):
        return True
    return any(
        has_permission(user, code)
        for code in WORKFLOW_PERMISSION_CODES
        if code != VIEW_PERMISSION
    )


def stage_permission_required(user, stage) -> bool:
    """اعتماد الطلبات — مدير الموارد (operations.approve_gm)."""
    if user.is_superuser:
        return True
    if _is_super_or_admin(user):
        return True
    from apps.core.models import PendingAction
    if stage in {
        PendingAction.Stage.BRANCH,
        PendingAction.Stage.GM,
        PendingAction.Stage.OFFICER,
    }:
        return (
            has_permission(user, 'operations.approve_gm')
            or has_permission(user, 'operations.approve_officer')
            or has_permission(user, 'operations.approve_branch')
            or has_permission(user, 'operations.approve_admin')
        )
    return False


def can_return_operation(user) -> bool:
    if user.is_superuser:
        return True
    return has_permission(user, RETURN_PERMISSION)


def can_resubmit_operation(user) -> bool:
    if user.is_superuser:
        return True
    return has_permission(user, RESUBMIT_PERMISSION)


def user_can_reject_employment_request(user, emp_req) -> bool:
    """رفض/إرجاع طلب توظيف — مدير الموارد فقط."""
    if not user or not getattr(user, 'is_authenticated', False) or not user.is_authenticated:
        return False
    if user.is_superuser or _is_super_or_admin(user):
        return True
    if not can_return_operation(user):
        return False

    from apps.employees.models import EmploymentRequest
    from apps.core.workflow_simple import is_simple_hr_manager

    status = emp_req.status
    pending = {
        EmploymentRequest.Status.PENDING_BRANCH,
        EmploymentRequest.Status.PENDING,
        EmploymentRequest.Status.PENDING_GM,
        EmploymentRequest.Status.PENDING_OFFICER,
    }
    if status in pending:
        return is_simple_hr_manager(user)
    return False


def can_delete_pending_action(user, action) -> bool:
    """حذف/إخفاء طلب عملية — الإدارة لكل الحالات؛ المقدّم لطلباته بما فيها المكتملة."""
    if not user or not getattr(user, 'is_authenticated', False) or not user.is_authenticated:
        return False
    if user.is_superuser or _is_super_or_admin(user):
        return True
    if action.requested_by_id == user.id:
        return action.status in (
            PendingAction.Status.RETURNED,
            PendingAction.Status.PENDING_BRANCH,
            PendingAction.Status.APPROVED,
        )
    return False


def can_delete_employment_request(user, emp_req) -> bool:
    """حذف/إخفاء طلب توظيف — الإدارة لكل الحالات؛ المقدّم لطلباته بما فيها المكتملة."""
    from apps.employees.models import EmploymentRequest

    if not user or not getattr(user, 'is_authenticated', False) or not user.is_authenticated:
        return False
    if user.is_superuser or _is_super_or_admin(user):
        return True
    if emp_req.requested_by_id == user.id:
        return emp_req.status in (
            EmploymentRequest.Status.PENDING_BRANCH,
            EmploymentRequest.Status.PENDING,
            EmploymentRequest.Status.REJECTED,
            EmploymentRequest.Status.APPROVED,
        )
    return False
