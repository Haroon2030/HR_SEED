"""
إعداد الأدوار — نموذج مبسّط (3 أدوار)
python manage.py setup_roles
python manage.py setup_roles --reset
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.core.models import Role, Permission
from apps.core.role_catalog import ROLE_CATALOG
from apps.core.workflow_simple import ACTIVE_ROLE_TYPES, LEGACY_ROLE_MIGRATION_MAP


def _role_meta(role_type: str) -> dict:
    entry = ROLE_CATALOG[role_type]
    return {
        'name': entry['name'],
        'description': entry['description'],
        'role_type': role_type,
        'is_system_role': True,
    }


class Command(BaseCommand):
    help = 'إنشاء الأدوار الثلاثة: أدمن، مدير موارد، موظف موارد'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='إعادة إنشاء الأدوار النظامية النشطة',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write(self.style.WARNING('👥 جاري إعداد الأدوار (3 أدوار)...'))

            if options['reset']:
                self.stdout.write(self.style.WARNING('⚠️  إعادة تعيين الأدوار النشطة...'))
                for role in Role.all_objects.filter(
                    is_system_role=True,
                    role_type__in=ACTIVE_ROLE_TYPES,
                ):
                    role.hard_delete()

            self.create_roles()
            self.deactivate_legacy_roles()
            self.migrate_legacy_user_roles()

            self.stdout.write(self.style.SUCCESS('✅ تم إعداد الأدوار بنجاح!'))

    def create_roles(self):
        all_permissions = {p.code: p for p in Permission.objects.select_related('module').all()}

        roles_config = [
            {
                **_role_meta(Role.RoleType.ADMIN),
                'permissions': 'all',
            },
            {
                **_role_meta(Role.RoleType.HR_MANAGER),
                'permissions': [
                    'employees.view', 'employees.add', 'employees.edit', 'employees.delete',
                    'employees.edit_absence', 'employees.delete_absence',
                    'employees.edit_statement', 'employees.delete_statement',
                    'employees.edit_loan', 'employees.delete_loan',
                    'employees.edit_ledger', 'employees.delete_ledger',
                    'employees.edit_leave', 'employees.delete_leave',
                    'departments.view', 'departments.add', 'departments.edit', 'departments.delete',
                    'branches.view', 'branches.add', 'branches.edit',
                    'payroll.view', 'payroll.manage', 'payroll.process', 'payroll.view_reports',
                    'users.view', 'users.add', 'users.edit',
                    'reports.view', 'reports.view_all',
                    'operations.view', 'operations.approve_gm', 'operations.return', 'operations.resubmit',
                    'attendance.view', 'attendance_screen_report.view',
                    'leaves.view', 'leaves.approve', 'leaves.manage',
                ],
            },
            {
                **_role_meta(Role.RoleType.SPECIALIST),
                'permissions': [
                    'employees.view', 'employees.edit',
                    'departments.view', 'branches.view',
                    'operations.view', 'operations.approve_officer', 'operations.resubmit',
                    'attendance.view',
                    'leaves.view',
                ],
            },
        ]

        for role_config in roles_config:
            role, created = Role.objects.update_or_create(
                role_type=role_config['role_type'],
                defaults={
                    'name': role_config['name'],
                    'description': role_config['description'],
                    'is_system_role': True,
                    'is_active': True,
                },
            )

            if role_config['permissions'] == 'all':
                role.permissions.set(all_permissions.values())
                perm_count = len(all_permissions)
            else:
                role_permissions = [
                    all_permissions[code]
                    for code in role_config['permissions']
                    if code in all_permissions
                ]
                role.permissions.set(role_permissions)
                perm_count = len(role_permissions)

            action = 'إنشاء' if created else 'تحديث'
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ تم {action} الدور: {role.name} ({perm_count} صلاحية)')
            )

    def deactivate_legacy_roles(self):
        deactivated = Role.objects.filter(is_system_role=True).exclude(
            role_type__in=ACTIVE_ROLE_TYPES,
        ).update(is_active=False)
        if deactivated:
            self.stdout.write(
                self.style.WARNING(f'  ○ عُطّل {deactivated} دور قديم غير مستخدم')
            )

    def migrate_legacy_user_roles(self):
        from apps.core.models import UserProfile

        migrated = 0
        for profile in UserProfile.objects.select_related('role').filter(role__isnull=False):
            old_type = profile.role.role_type
            if old_type in ACTIVE_ROLE_TYPES:
                continue
            new_type = LEGACY_ROLE_MIGRATION_MAP.get(old_type)
            if not new_type:
                continue
            new_role = Role.objects.filter(role_type=new_type, is_active=True).first()
            if not new_role:
                continue
            profile.role = new_role
            profile.save(update_fields=['role'])
            migrated += 1
        if migrated:
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ رُحّل {migrated} مستخدم إلى الأدوار الجديدة')
            )
