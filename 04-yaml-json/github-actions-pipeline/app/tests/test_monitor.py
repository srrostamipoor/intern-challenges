from unittest.mock import patch

import requests

from monitor import check_url


def test_check_url_returns_true_on_200():
    with patch("monitor.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        is_up, reason = check_url("http://example.com")
    assert is_up is True


def test_check_url_returns_false_on_500():
    with patch("monitor.requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        is_up, reason = check_url("http://example.com")
    assert is_up is False


def test_check_url_handles_connection_error():
    error = requests.exceptions.ConnectionError
    with patch("monitor.requests.get", side_effect=error):
        is_up, reason = check_url("http://doesnotexist.internal")
    assert is_up is False
    assert "connection" in reason.lower()
