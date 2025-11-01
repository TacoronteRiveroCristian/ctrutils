"""Tests unitarios para LokiHandler"""

import logging
from unittest.mock import Mock, patch, call

import pytest

from ctrutils.handler.notification.loki_handler import LokiHandler


class TestLokiHandler:
    """Test suite para LokiHandler"""

    @patch('ctrutils.handler.notification.loki_handler.REQUESTS_AVAILABLE', True)
    def test_init_success(self):
        """Test inicialización exitosa de LokiHandler"""
        handler = LokiHandler(
            url="http://localhost:3100",
            labels={"app": "test", "env": "dev"},
            level=logging.INFO,
            timeout=5,
            batch_size=0
        )

        assert handler.url == "http://localhost:3100/loki/api/v1/push"
        assert handler.labels == {"app": "test", "env": "dev"}
        assert handler.timeout == 5
        assert handler.batch_size == 0
        assert handler.batch == []

    @patch('ctrutils.handler.notification.loki_handler.REQUESTS_AVAILABLE', False)
    def test_init_no_requests(self):
        """Test error cuando requests no está disponible"""
        with pytest.raises(ImportError, match="'requests' es requerido"):
            LokiHandler(
                url="http://localhost:3100",
                labels={"app": "test"}
            )

    @patch('ctrutils.handler.notification.loki_handler.REQUESTS_AVAILABLE', True)
    def test_url_normalization(self):
        """Test normalización de URL (remover trailing slash)"""
        handler = LokiHandler(
            url="http://localhost:3100/",
            labels={"app": "test"}
        )

        assert handler.url == "http://localhost:3100/loki/api/v1/push"

    @patch('ctrutils.handler.notification.loki_handler.REQUESTS_AVAILABLE', True)
    @patch('ctrutils.handler.notification.loki_handler.requests.post')
    @patch('time.time', return_value=1000.0)
    def test_emit_without_batching(self, mock_time, mock_post):
        """Test envío inmediato de log sin batching"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        handler = LokiHandler(
            url="http://localhost:3100",
            labels={"app": "test"},
            batch_size=0
        )
        handler.setFormatter(logging.Formatter('%(message)s'))

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )

        handler.emit(record)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:3100/loki/api/v1/push"
        assert call_args[1]['json']['streams'][0]['stream'] == {"app": "test"}
        assert call_args[1]['json']['streams'][0]['values'][0][1] == "Test message"

    @patch('ctrutils.handler.notification.loki_handler.REQUESTS_AVAILABLE', True)
    @patch('ctrutils.handler.notification.loki_handler.requests.post')
    @patch('time.time', return_value=1000.0)
    def test_emit_with_batching(self, mock_time, mock_post):
        """Test acumulación de logs con batching"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        handler = LokiHandler(
            url="http://localhost:3100",
            labels={"app": "test"},
            batch_size=3
        )
        handler.setFormatter(logging.Formatter('%(message)s'))

        # Enviar 2 logs (no debe enviar aún)
        for i in range(2):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"Message {i}",
                args=(),
                exc_info=None
            )
            handler.emit(record)

        assert len(handler.batch) == 2
        mock_post.assert_not_called()

        # Enviar el tercer log (debe enviar el batch)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Message 2",
            args=(),
            exc_info=None
        )
        handler.emit(record)

        assert len(handler.batch) == 0
        mock_post.assert_called_once()

    @patch('ctrutils.handler.notification.loki_handler.REQUESTS_AVAILABLE', True)
    @patch('ctrutils.handler.notification.loki_handler.requests.post')
    @patch('time.time', return_value=1000.0)
    def test_flush_with_pending_batch(self, mock_time, mock_post):
        """Test flush envía logs pendientes"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        handler = LokiHandler(
            url="http://localhost:3100",
            labels={"app": "test"},
            batch_size=10
        )
        handler.setFormatter(logging.Formatter('%(message)s'))

        # Agregar log sin alcanzar batch_size
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        handler.emit(record)

        assert len(handler.batch) == 1
        mock_post.assert_not_called()

        # Flush debe enviar el batch pendiente
        handler.flush()

        assert len(handler.batch) == 0
        mock_post.assert_called_once()

    @patch('ctrutils.handler.notification.loki_handler.REQUESTS_AVAILABLE', True)
    @patch('ctrutils.handler.notification.loki_handler.requests.post')
    def test_emit_http_error(self, mock_post, capsys):
        """Test manejo de errores HTTP"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        handler = LokiHandler(
            url="http://localhost:3100",
            labels={"app": "test"}
        )
        handler.setFormatter(logging.Formatter('%(message)s'))

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )

        handler.emit(record)

        captured = capsys.readouterr()
        assert "Loki respondió con status 500" in captured.err

    @patch('ctrutils.handler.notification.loki_handler.REQUESTS_AVAILABLE', True)
    @patch('ctrutils.handler.notification.loki_handler.requests.post')
    def test_emit_timeout(self, mock_post, capsys):
        """Test manejo de timeout"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")

        handler = LokiHandler(
            url="http://localhost:3100",
            labels={"app": "test"}
        )
        handler.setFormatter(logging.Formatter('%(message)s'))

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )

        handler.emit(record)

        captured = capsys.readouterr()
        assert "Timeout al enviar logs a Loki" in captured.err

    @patch('ctrutils.handler.notification.loki_handler.REQUESTS_AVAILABLE', True)
    @patch('ctrutils.handler.notification.loki_handler.requests.post')
    def test_close_sends_pending_logs(self, mock_post):
        """Test close envía logs pendientes antes de cerrar"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        handler = LokiHandler(
            url="http://localhost:3100",
            labels={"app": "test"},
            batch_size=10
        )
        handler.setFormatter(logging.Formatter('%(message)s'))

        # Agregar log
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        handler.emit(record)

        assert len(handler.batch) == 1

        # Close debe enviar logs pendientes
        handler.close()

        assert len(handler.batch) == 0
        mock_post.assert_called_once()
