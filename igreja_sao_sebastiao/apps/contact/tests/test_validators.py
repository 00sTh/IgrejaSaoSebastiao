import pytest
from django.core.exceptions import ValidationError

from apps.contact.validators import (
    validate_brazilian_phone,
    validate_email_not_disposable,
    validate_name_brazilian,
)


class TestBrazilianPhoneValidator:
    def test_valid_landline(self):
        validate_brazilian_phone("3132951379")  # 10 digits

    def test_valid_mobile(self):
        validate_brazilian_phone("31988886796")  # 11 digits

    def test_valid_with_formatting(self):
        validate_brazilian_phone("(31) 98888-6796")

    def test_invalid_too_short(self):
        with pytest.raises(ValidationError):
            validate_brazilian_phone("123456789")

    def test_invalid_ddd(self):
        with pytest.raises(ValidationError):
            validate_brazilian_phone("0012345678")

    def test_invalid_mobile_no_9(self):
        with pytest.raises(ValidationError):
            validate_brazilian_phone("31188886796")  # 11 digits but no 9 prefix


class TestEmailNotDisposable:
    def test_valid_email(self):
        validate_email_not_disposable("joao@gmail.com")

    def test_blocked_domain(self):
        with pytest.raises(ValidationError):
            validate_email_not_disposable("test@mailinator.com")

    def test_blocked_domain_yopmail(self):
        with pytest.raises(ValidationError):
            validate_email_not_disposable("test@yopmail.com")


class TestNameBrazilian:
    def test_valid_full_name(self):
        validate_name_brazilian("João Silva")

    def test_valid_three_names(self):
        validate_name_brazilian("Maria José Santos")

    def test_single_name(self):
        with pytest.raises(ValidationError):
            validate_name_brazilian("João")

    def test_short_word(self):
        with pytest.raises(ValidationError):
            validate_name_brazilian("J Silva")
