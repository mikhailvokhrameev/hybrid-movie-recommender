import json
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest

from core.ollama_client import (
    aclassify_message,
    aparse_intent,
    _extract_intent,
    _fallback_intent,
    parse_intent,
)


class TestClassifyMessage:
    @pytest.mark.asyncio
    async def test_returns_valid_category(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": json.dumps({"category": "follow_up"})}
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("core.ollama_client.httpx.AsyncClient", return_value=mock_client):
            result = await aclassify_message("расскажи про первый фильм")
            assert result == "follow_up"

    @pytest.mark.asyncio
    async def test_invalid_category_defaults_to_new_search(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": json.dumps({"category": "invalid_type"})}
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("core.ollama_client.httpx.AsyncClient", return_value=mock_client):
            result = await aclassify_message("test")
            assert result == "new_search"

    @pytest.mark.asyncio
    async def test_http_error_defaults_to_new_search(self):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection failed"))

        with patch("core.ollama_client.httpx.AsyncClient", return_value=mock_client):
            result = await aclassify_message("test")
            assert result == "new_search"


class TestExtractIntent:
    def test_extracts_all_fields(self):
        parsed = {
            "genres": ["Комедии"],
            "mood": "happy",
            "themes": ["семья"],
            "negations": ["Ужасы"],
            "reference_films": ["Один дома"],
        }
        result = _extract_intent(parsed)
        assert result["mood"] == "happy"
        assert result["themes"] == ["семья"]
        assert result["reference_films"] == ["Один дома"]

    def test_missing_fields_default_to_empty(self):
        result = _extract_intent({})
        assert result["genres"] == []
        assert result["mood"] == ""
        assert result["themes"] == []
        assert result["negations"] == []
        assert result["reference_films"] == []


class TestFallbackIntent:
    def test_returns_empty_structure(self):
        result = _fallback_intent("any query")
        assert result["genres"] == []
        assert result["mood"] == ""
        assert result["themes"] == []
        assert result["negations"] == []
        assert result["reference_films"] == []
