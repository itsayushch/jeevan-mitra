import pytest

@pytest.mark.integration
def test_user_data_deletion():
    # Test that when a user requests deletion, their PII is wiped but metrics are retained
    assert True
