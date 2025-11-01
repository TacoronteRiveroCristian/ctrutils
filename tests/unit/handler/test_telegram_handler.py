"""Tests unitarios para TelegramBotHandler"""

import logging
from unittest.mock import Mock, patch

import pytest

from ctrutils.handler.notification.telegram_handler import TelegramBotHandler


class TestTelegramBotHandler:
    """Test suite para TelegramBotHandler"""

    @patch('ctrutils.handler.notification.telegram_handler.REQUESTS_AVAILABLE', True)
    def test_init_success(self):
        """Test inicialización exitosa de TelegramBotHandler"""
        handler = TelegramBotHandler(
            token="123456:ABC-DEF",
            chat_id="123456789",
            level=logging.ERROR,
            parse_mode="HTML",
            timeout=20
        )

        assert handler.token == "123456:ABC-DEF"
        assert handler.chat_id == "123456789"
        assert handler.parse_mode == "HTML"
        assert handler.timeout == 20
        assert "bot123456:ABC-DEF/sendMessage" in handler.api_url

    @patch('ctrutils.handler.notification.telegram_handler.REQUESTS_AVAILABLE', False)
    def test_init_no_requests(self):
        """Test error cuando requests no está disponible"""
        with pytest.raises(ImportError, match="'requests' es requerido"):
            TelegramBotHandler(
                token="test_token",
                chat_id="test_chat_id"
            )

    @patch('ctrutils.handler.notification.telegram_handler.REQUESTS_AVAILABLE', True)
    @patch('ctrutils.handler.notification.telegram_handler.requests.post')
    def test_emit_success(self, mock_post):
        """Test envío exitoso de mensaje a Telegram"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        handler = TelegramBotHandler(
            token="test_token",
            chat_id="test_chat_id",
            level=logging.ERROR
        )
        handler.setFormatter(logging.Formatter('%(message)s'))

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Test error message",
            args=(),
            exc_info=None
        )

        handler.emit(record)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "sendMessage" in call_args[0][0]
        assert call_args[1]['json']['chat_id'] == "test_chat_id"
        assert "Test error message" in call_args[1]['json']['text']
        assert call_args[1]['json']['parse_mode'] == "HTML"

    @patch('ctrutils.handler.notification.telegram_handler.REQUESTS_AVAILABLE', True)
    @patch('ctrutils.handler.notification.telegram_handler.requests.post')
    def test_emit_with_emoji(self, mock_post):
        """Test que el mensaje incluye emoji según el nivel"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        handler = TelegramBotHandler(
            token="test_token",
            chat_id="test_chat_id"
        )
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

        # Test ERROR
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Error message",
            args=(),
            exc_info=None
        )
        handler.emit(record)

        call_args = mock_post.call_args
        message = call_args[1]['json']['text']
        assert "❌" in message  # Error emoji

    @patch('ctrutils.handler.notification.telegram_handler.REQUESTS_AVAILABLE', True)
    @patch('ctrutils.handler.notification.telegram_handler.requests.post')
    def test_emit_long_message_truncation(self, mock_post):
        """Test truncamiento de mensajes largos"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        handler = TelegramBotHandler(
            token="test_token",
            chat_id="test_chat_id"
        )
        handler.setFormatter(logging.Formatter('%(message)s'))

        # Mensaje muy largo (>4000 caracteres)
        long_message = "A" * 5000
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg=long_message,
            args=(),
            exc_info=None
        )

        handler.emit(record)

        call_args = mock_post.call_args
        message = call_args[1]['json']['text']
        assert len(message) <= 4000
        assert message.endswith("...")

    @patch('ctrutils.handler.notification.telegram_handler.REQUESTS_AVAILABLE', True)
    @patch('ctrutils.handler.notification.telegram_handler.requests.post')
    def test_emit_http_error(self, mock_post, capsys):
        """Test manejo de errores HTTP"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        handler = TelegramBotHandler(
            token="test_token",
            chat_id="test_chat_id"
        )
        handler.setFormatter(logging.Formatter('%(message)s'))

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )

        handler.emit(record)

        captured = capsys.readouterr()
        assert "Telegram respondió con status 400" in captured.err

    @patch('ctrutils.handler.notification.telegram_handler.REQUESTS_AVAILABLE', True)
    @patch('ctrutils.handler.notification.telegram_handler.requests.post')
    def test_emit_timeout(self, mock_post, capsys):
        """Test manejo de timeout"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")

        handler = TelegramBotHandler(
            token="test_token",
            chat_id="test_chat_id"
        )
        handler.setFormatter(logging.Formatter('%(message)s'))

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )

        handler.emit(record)

        captured = capsys.readouterr()
        assert "Timeout al enviar mensaje a Telegram" in captured.err

    @patch('ctrutils.handler.notification.telegram_handler.REQUESTS_AVAILABLE', True)
    @patch('ctrutils.handler.notification.telegram_handler.requests.post')
    def test_emit_network_error(self, mock_post, capsys):
        """Test manejo de errores de red"""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        handler = TelegramBotHandler(
            token="test_token",
            chat_id="test_chat_id"
        )
        handler.setFormatter(logging.Formatter('%(message)s'))

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )

        handler.emit(record)

        captured = capsys.readouterr()
        assert "Error de red al enviar mensaje a Telegram" in captured.err

    @patch('ctrutils.handler.notification.telegram_handler.REQUESTS_AVAILABLE', True)
    def test_get_emoji_for_level(self):
        """Test obtención de emoji según nivel de log"""
        handler = TelegramBotHandler(
            token="test_token",
            chat_id="test_chat_id"
        )

        assert handler._get_emoji_for_level("DEBUG") == "🐛"
        assert handler._get_emoji_for_level("INFO") == "ℹ️"
        assert handler._get_emoji_for_level("WARNING") == "⚠️"
        assert handler._get_emoji_for_level("ERROR") == "❌"
        assert handler._get_emoji_for_level("CRITICAL") == "🚨"
        assert handler._get_emoji_for_level("UNKNOWN") == "📝"

    @patch('ctrutils.handler.notification.telegram_handler.REQUESTS_AVAILABLE', True)
    @patch('ctrutils.handler.notification.telegram_handler.requests.post')
    def test_emit_different_parse_modes(self, mock_post):
        """Test diferentes parse modes"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Test HTML
        handler_html = TelegramBotHandler(
            token="test_token",
            chat_id="test_chat_id",
            parse_mode="HTML"
        )
        handler_html.setFormatter(logging.Formatter('%(message)s'))

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="<b>Bold</b>",
            args=(),
            exc_info=None
        )
        handler_html.emit(record)

        call_args = mock_post.call_args
        assert call_args[1]['json']['parse_mode'] == "HTML"

        # Test Markdown
        handler_md = TelegramBotHandler(
            token="test_token",
            chat_id="test_chat_id",
            parse_mode="Markdown"
        )
        handler_md.setFormatter(logging.Formatter('%(message)s'))
        handler_md.emit(record)

        call_args = mock_post.call_args
        assert call_args[1]['json']['parse_mode'] == "Markdown"
