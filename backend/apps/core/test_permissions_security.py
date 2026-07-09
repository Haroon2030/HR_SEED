"""اختبارات أمان نظام الصلاحيات."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.core.forms import RoleForm
from apps.core.models import Branch, Company, Permission, Role, UserProfile

User = get_user_model()


@override_settings(ALLOWED_HOSTS=['testserver'])
class RoleTypeEscalationTests(TestCase):
    def setUp(self):
        company = Company.objects.create(name='شركة اختبار')
        self.branch = Branch.objects.create(name='فرع 1', code='SEC1', company=company)
        self.manager_role = Role.objects.create(
            name='مدير فرع اختبار',
            role_type=Role.RoleType.MANAGER,
            is_system_role=False,
        )
        perm, _ = Permission.objects.get_or_create(
            code='users.manage_roles',
            defaults={'name': 'إدارة الأدوار', 'operation': 'manage_roles', 'is_active': True},
        )
        self.manager_role.permissions.add(perm)
        self.manager = User.objects.create_user(username='branch_mgr', password='pass')
        profile = self.manager.profile
        profile.role = self.manager_role
        profile.branch = self.branch
        profile.save(update_fields=['role', 'branch'])

        self.target_role = Role.objects.create(
            name='دور موظف',
            role_type=Role.RoleType.EMPLOYEE,
            is_system_role=False,
        )

    def test_non_superuser_cannot_escalate_role_type_to_admin_via_form(self):
        form = RoleForm(
            data={
                'name': self.target_role.name,
                'role_type': Role.RoleType.ADMIN,
                'description': '',
                'is_active': '1',
            },
            instance=self.target_role,
            actor=self.manager,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('role_type', form.errors)

    def test_non_superuser_cannot_create_admin_role_via_form(self):
        form = RoleForm(
            data={
                'name': 'دور أدمن جديد',
                'role_type': Role.RoleType.ADMIN,
                'description': '',
                'is_active': '1',
            },
            actor=self.manager,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('role_type', form.errors)
