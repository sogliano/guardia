import pytest
from unittest.mock import patch

from app.core.security import verify_clerk_token


class TestSecurity:
    @patch("app.core.security.settings")
    def test_verify_clerk_token_valid(self, mock_settings):
        """Test is a placeholder — requires a real RS256 keypair to test properly."""
        pass

    def test_verify_clerk_token_invalid(self):
        from jwt.exceptions import PyJWTError

        with pytest.raises(Exception):
            verify_clerk_token("invalid-token")
