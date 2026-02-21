import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.check_password("testpass123")
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        user = User.objects.create_superuser(username="admin", email="admin@example.com", password="adminpass")
        assert user.is_staff
        assert user.is_superuser

    def test_user_str(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass",
            first_name="João",
            last_name="Silva",
        )
        assert str(user) == "João Silva"

    def test_user_str_no_name(self):
        user = User.objects.create_user(username="testuser", email="test@example.com", password="pass")
        assert str(user) == "testuser"

    def test_failed_login_attempts_default(self):
        user = User.objects.create_user(username="testuser", email="test@example.com", password="pass")
        assert user.failed_login_attempts == 0
        assert user.last_failed_login is None


@pytest.mark.django_db
class TestAuditLog:
    def test_create_audit_log(self):
        from apps.accounts.models import AuditLog

        user = User.objects.create_user(username="admin", email="admin@example.com", password="pass")
        log = AuditLog.objects.create(
            user=user,
            action="login",
            entity_type="user",
            entity_id=str(user.pk),
            ip_address="127.0.0.1",
        )
        assert "admin" in str(log)
        assert "login" in str(log)

    def test_audit_log_without_user(self):
        from apps.accounts.models import AuditLog

        log = AuditLog.objects.create(action="system_start")
        assert "sistema" in str(log)
