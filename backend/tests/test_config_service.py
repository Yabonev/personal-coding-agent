"""Tests for ConfigService."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from src.config.config_service import ConfigService


class TestConfigService:
    """Tests for ConfigService."""

    @patch("src.config.config_service.load_dotenv")
    def test_get_api_key_success(self, mock_load_dotenv):
        """Test getting API key when it exists."""
        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key-123"}):
            service = ConfigService()
            api_key = service.get_api_key()

            assert api_key == "test-key-123"
            mock_load_dotenv.assert_called_once()

    @patch("src.config.config_service.load_dotenv")
    def test_get_api_key_missing_raises_error(self, mock_load_dotenv):
        """Test getting API key when it doesn't exist raises error."""
        with patch.dict(os.environ, {}, clear=True):
            service = ConfigService()

            with pytest.raises(ValueError, match="ZAI_API_KEY not found"):
                service.get_api_key()

    @patch("src.config.config_service.load_dotenv")
    def test_get_api_key_empty_raises_error(self, mock_load_dotenv):
        """Test getting API key when it's empty raises error."""
        with patch.dict(os.environ, {"ZAI_API_KEY": ""}):
            service = ConfigService()

            with pytest.raises(ValueError, match="ZAI_API_KEY not found"):
                service.get_api_key()

    @patch("src.config.config_service.load_dotenv")
    def test_create_chat_config_with_defaults(self, mock_load_dotenv):
        """Test creating config with default values."""
        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            service = ConfigService()
            config = service.create_chat_config()

            assert config.api_key == "test-key"
            assert config.base_url == "https://api.z.ai/api/coding/paas/v4"
            assert config.model == "glm-4.7"
            assert config.system_prompt

    @patch("src.config.config_service.load_dotenv")
    def test_create_chat_config_with_overrides(self, mock_load_dotenv):
        """Test creating config with custom values."""
        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            service = ConfigService()
            config = service.create_chat_config(
                base_url="https://custom.api.com",
                model="custom-model",
                system_prompt="Custom prompt",
            )

            assert config.api_key == "test-key"
            assert config.base_url == "https://custom.api.com"
            assert config.model == "custom-model"
            assert config.system_prompt == "Custom prompt"

    @patch("src.config.config_service.load_dotenv")
    def test_create_chat_config_partial_overrides(self, mock_load_dotenv):
        """Test creating config with some custom values."""
        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            service = ConfigService()
            config = service.create_chat_config(model="custom-model")

            assert config.api_key == "test-key"
            assert config.base_url == "https://api.z.ai/api/coding/paas/v4"  # Default
            assert config.model == "custom-model"  # Override
            assert config.system_prompt  # Default
