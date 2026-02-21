import pytest

from apps.accounts.models import User


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="testpass123",
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username="user",
        email="user@test.com",
        password="testpass123",
    )


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client


@pytest.fixture
def seeded_content(db):
    """Run seed_content command and return."""
    from django.core.management import call_command

    call_command("seed_content", verbosity=0)
