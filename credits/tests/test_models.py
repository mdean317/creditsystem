from django.test import TestCase
from credits.models import CreditPackage
from django.utils import timezone
import pytest
from django.core.exceptions import ValidationError

'''Tests for Model Credit Package'''
def test_create_credit_package_defaults():
    package = CreditPackage.objects.create(
        name="Pack 1",
        credit_amount=100,
        price_cents=999,
    )

    assert package.id is not None
    assert package.is_active is True
    assert package.description == ""
    assert isinstance(package.created_at, timezone.datetime)
    assert isinstance(package.updated_at, timezone.datetime)

def test_str_representation():
    package = CreditPackage.objects.create(
        name="Pack 2",
        credit_amount=500,
        price_cents=4999,
    )
    assert str(package) == "Pack 2 - 500 credits"

def test_missing_required_fields():
    package = CreditPackage(
        credit_amount=100,
        price_cents=1000,
    )
    with pytest.raises(ValidationError):
        package.full_clean() 

def test_negative_credit_amount_invalid():
    package = CreditPackage(
        name="Negative Pack",
        credit_amount=-10,
        price_cents=500
    )
    with pytest.raises(ValidationError):
        package.full_clean()

def test_zero_price_is_valid():
    package = CreditPackage(
        name="Free Trial",
        credit_amount=10,
        price_cents=0
    )
    package.full_clean()  # Should not raise an error


def test_updating_fields():
    package = CreditPackage.objects.create(
        name="package 10",
        credit_amount=100,
        price_cents=1000
    )
    package.credit_amount = 200
    package.save()
    package.refresh_from_db()
    assert package.credit_amount == 200

def test_filter_active_packages():
    active = CreditPackage.objects.create(name="Active", credit_amount=100, price_cents=1000, is_active=True)
    inactive = CreditPackage.objects.create(name="Inactive", credit_amount=100, price_cents=1000, is_active=False)

    active_packages = CreditPackage.objects.filter(is_active=True)
    assert active in active_packages
    assert inactive not in active_packages
    
def test_ordering_by_created_at():
    older = CreditPackage.objects.create(name="Old", credit_amount=100, price_cents=500)
    newer = CreditPackage.objects.create(name="New", credit_amount=200, price_cents=1000)

    results = CreditPackage.objects.order_by("-created_at")
    assert results.first() == newer
    assert results.last() == older
