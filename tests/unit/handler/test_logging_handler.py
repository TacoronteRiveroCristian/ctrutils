"""Tests unitarios para LoggingHandler"""

import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ctrutils.handler import LoggingHandler


class TestLoggingHandler:
    """Test suite para LoggingHandler"""

    def test_init_default(self):
        """Test inicialización con valores por defecto"""
        handler = LoggingHandler()
        assert handler._level == logging.INFO
        assert handler._message_format is not None
        assert handler.logger is not None
        assert handler.logger.propagate is False

    def test_init_custom(self):
        """Test inicialización con valores personalizados"""
        handler = LoggingHandler(
            level=logging.DEBUG,
            message_format="%(message)s",
            logger_name="custom_logger"
        )
        assert handler._level == logging.DEBUG
        assert handler._message_format == "%(message)s"
        assert handler._logger_name == "custom_logger"

    def test_create_stream_handler(self):
        """Test creación de StreamHandler"""
        handler = LoggingHandler()
        stream_handler = handler.create_stream_handler()

        assert isinstance(stream_handler, logging.StreamHandler)
        assert stream_handler.level == logging.INFO

    def test_create_file_handler(self, tmp_path):
        """Test creación de FileHandler"""
        handler = LoggingHandler()
        log_file = tmp_path / "test.log"
        file_handler = handler.create_file_handler(str(log_file))

        assert isinstance(file_handler, logging.FileHandler)
        assert log_file.exists()

    def test_create_size_rotating_file_handler(self, tmp_path):
        """Test creación de RotatingFileHandler"""
        handler = LoggingHandler()
        log_file = tmp_path / "rotating.log"

        rotating_handler = handler.create_size_rotating_file_handler(
            log_file=str(log_file),
            max_bytes=1024,
            backup_count=3
        )

        assert isinstance(rotating_handler, logging.handlers.RotatingFileHandler)
        assert rotating_handler.maxBytes == 1024
        assert rotating_handler.backupCount == 3

    def test_create_timed_rotating_file_handler(self, tmp_path):
        """Test creación de TimedRotatingFileHandler"""
        handler = LoggingHandler()
        log_file = tmp_path / "timed.log"

        timed_handler = handler.create_timed_rotating_file_handler(
            log_file=str(log_file),
            when="D",
            interval=1,
            backup_count=7
        )

        assert isinstance(timed_handler, logging.handlers.TimedRotatingFileHandler)
        assert timed_handler.when == "D"
        # El interval se convierte a segundos internamente (1 día = 86400 segundos)
        assert timed_handler.interval == 86400
        assert timed_handler.backupCount == 7

    def test_add_handlers(self):
        """Test agregar handlers al logger"""
        handler = LoggingHandler()
        stream_handler = handler.create_stream_handler()

        logger = handler.add_handlers([stream_handler])

        assert logger is not None
        assert len(logger.handlers) >= 1
        assert stream_handler in logger.handlers

    def test_remove_handlers_all(self):
        """Test eliminar todos los handlers"""
        handler = LoggingHandler()
        stream_handler = handler.create_stream_handler()
        logger = handler.add_handlers([stream_handler])

        handler.remove_handlers(remove_all=True)

        assert handler.logger is None

    def test_quick_console_logger(self):
        """Test método estático quick_console_logger"""
        logger = LoggingHandler.quick_console_logger("test_app", logging.DEBUG)

        assert logger is not None
        assert logger.name == "test_app"
        assert logger.level == logging.DEBUG

    def test_quick_file_logger(self, tmp_path):
        """Test método estático quick_file_logger"""
        log_file = tmp_path / "app.log"
        logger = LoggingHandler.quick_file_logger(
            "test_app",
            str(log_file),
            logging.INFO
        )

        assert logger is not None
        assert logger.name == "test_app"
        assert Path(log_file).exists()

    @patch('ctrutils.handler.logging.logging_handler.LOKI_AVAILABLE', True)
    @patch('ctrutils.handler.logging.logging_handler.LokiHandler')
    def test_create_loki_handler_available(self, mock_loki_class):
        """Test creación de LokiHandler cuando está disponible"""
        handler = LoggingHandler()
        mock_loki_instance = Mock()
        mock_loki_class.return_value = mock_loki_instance

        loki_handler = handler.create_loki_handler(
            url="http://localhost:3100",
            labels={"app": "test"}
        )

        assert loki_handler == mock_loki_instance
        mock_loki_class.assert_called_once()

    @patch('ctrutils.handler.logging.logging_handler.LOKI_AVAILABLE', False)
    def test_create_loki_handler_not_available(self):
        """Test error cuando LokiHandler no está disponible"""
        handler = LoggingHandler()

        with pytest.raises(ImportError, match="LokiHandler no está disponible"):
            handler.create_loki_handler(
                url="http://localhost:3100",
                labels={"app": "test"}
            )

    @patch('ctrutils.handler.logging.logging_handler.TELEGRAM_AVAILABLE', True)
    @patch('ctrutils.handler.logging.logging_handler.TelegramBotHandler')
    def test_create_telegram_handler_available(self, mock_telegram_class):
        """Test creación de TelegramBotHandler cuando está disponible"""
        handler = LoggingHandler()
        mock_telegram_instance = Mock()
        mock_telegram_class.return_value = mock_telegram_instance

        telegram_handler = handler.create_telegram_handler(
            token="test_token",
            chat_id="test_chat_id"
        )

        assert telegram_handler == mock_telegram_instance
        mock_telegram_class.assert_called_once()

    @patch('ctrutils.handler.logging.logging_handler.TELEGRAM_AVAILABLE', False)
    def test_create_telegram_handler_not_available(self):
        """Test error cuando TelegramBotHandler no está disponible"""
        handler = LoggingHandler()

        with pytest.raises(ImportError, match="TelegramBotHandler no está disponible"):
            handler.create_telegram_handler(
                token="test_token",
                chat_id="test_chat_id"
            )

    @patch('sys.exit')
    def test_log_exception_and_exit(self, mock_exit):
        """Test método log_exception_and_exit"""
        handler = LoggingHandler()
        logger = handler.add_handlers([handler.create_stream_handler()])

        test_exception = Exception("Test error")

        handler.log_exception_and_exit(
            test_exception,
            exit_code=1,
            context={"test": "context"}
        )

        mock_exit.assert_called_once_with(1)

    def test_log_exception_and_exit_no_logger(self):
        """Test log_exception_and_exit sin logger configurado"""
        handler = LoggingHandler()
        handler.logger = None

        with pytest.raises(ValueError, match="No se ha configurado ningún logger"):
            handler.log_exception_and_exit(Exception("Test"))
