import unittest
from unittest.mock import patch

from app.entitlements import get_license_status


class GetLicenseStatusTests(unittest.TestCase):
    @patch("app.entitlements.get_license_field", return_value=None)
    def test_returns_invalid_when_license_cannot_be_verified(self, _mock_field):
        status = get_license_status()

        self.assertFalse(status["valid"])
        self.assertIsNone(status["expires_at"])
        self.assertIn("Unable to verify", status["reason"])

    @patch("app.entitlements.get_license_field", return_value={"value": ""})
    def test_empty_expiration_never_expires(self, _mock_field):
        self.assertEqual(
            get_license_status(),
            {"valid": True, "expires_at": None, "reason": None},
        )

    @patch(
        "app.entitlements.get_license_field",
        return_value={"value": "2999-01-01T00:00:00Z"},
    )
    def test_future_expiration_is_valid(self, _mock_field):
        status = get_license_status()

        self.assertTrue(status["valid"])
        self.assertEqual(status["expires_at"], "2999-01-01T00:00:00Z")
        self.assertIsNone(status["reason"])

    @patch(
        "app.entitlements.get_license_field",
        return_value={"value": "2000-01-01T00:00:00Z"},
    )
    def test_past_expiration_is_invalid(self, _mock_field):
        status = get_license_status()

        self.assertFalse(status["valid"])
        self.assertIn("expired", status["reason"].lower())

    @patch("app.entitlements.get_license_field", return_value={"value": "not-a-date"})
    def test_malformed_expiration_is_invalid(self, _mock_field):
        status = get_license_status()

        self.assertFalse(status["valid"])
        self.assertEqual(status["expires_at"], "not-a-date")
        self.assertIn("Invalid", status["reason"])


if __name__ == "__main__":
    unittest.main()
