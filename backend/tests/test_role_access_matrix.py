import pytest

# Mock definitions for testing purposes
roles = ["anonymous", "beneficiary", "counselor", "catalogue_admin", "analyst", "super_admin"]

def get_role_access(role, endpoint):
    matrix = {
        "anonymous": [],
        "beneficiary": ["/api/v1/interview", "/api/v1/recommendations"],
        "counselor": ["/api/v1/interview", "/api/v1/recommendations"],
        "catalogue_admin": ["/api/v1/catalogue/manage"],
        "analyst": ["/api/v1/monitoring/admin/system/status", "/api/v1/monitoring/admin/system/quality-summary"],
        "super_admin": ["/api/v1/interview", "/api/v1/recommendations", "/api/v1/catalogue/manage", "/api/v1/monitoring/admin/system/status", "/api/v1/monitoring/admin/system/quality-summary"]
    }
    return endpoint in matrix.get(role, [])

def test_anonymous_access():
    assert not get_role_access("anonymous", "/api/v1/interview")

def test_beneficiary_access():
    assert get_role_access("beneficiary", "/api/v1/interview")
    assert not get_role_access("beneficiary", "/api/v1/monitoring/admin/system/status")

def test_counselor_access():
    assert get_role_access("counselor", "/api/v1/interview")
    assert not get_role_access("counselor", "/api/v1/monitoring/admin/system/status")

def test_catalogue_admin_access():
    assert get_role_access("catalogue_admin", "/api/v1/catalogue/manage")
    assert not get_role_access("catalogue_admin", "/api/v1/interview")

def test_analyst_access():
    assert get_role_access("analyst", "/api/v1/monitoring/admin/system/status")
    assert not get_role_access("analyst", "/api/v1/interview")

def test_super_admin_access():
    assert get_role_access("super_admin", "/api/v1/monitoring/admin/system/status")
    assert get_role_access("super_admin", "/api/v1/interview")
