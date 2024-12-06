import pytest
import logging
import asyncio
from unittest.mock import MagicMock, patch
from telegram import Bot
from telegram.error import TelegramError
from tgbot_logging import TelegramHandler

@pytest.fixture
def mock_bot():
    with patch('tgbot_logging.handler.Bot') as mock:
        yield mock

@pytest.fixture
def handler(mock_bot):
    return TelegramHandler(
        token='test_token',
        chat_ids=['123456789'],
        batch_size=2,
        batch_interval=0.1
    )

def test_init(handler):
    """Test handler initialization."""
    assert handler.token == 'test_token'
    assert handler.chat_ids == ['123456789']
    assert handler.batch_size == 2
    assert handler.batch_interval == 0.1
    assert handler.parse_mode == 'HTML'
    assert not handler.is_closed

def test_format_message_html(handler):
    """Test message formatting with HTML mode."""
    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test message with <b>HTML</b>',
        args=(),
        exc_info=None
    )
    
    formatted = handler._format_message(record)
    assert '<b>HTML</b>' in formatted

def test_format_message_markdown(mock_bot):
    """Test message formatting with MarkdownV2 mode."""
    handler = TelegramHandler(
        token='test_token',
        chat_ids=['123456789'],
        parse_mode='MarkdownV2'
    )
    
    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test message with *bold*',
        args=(),
        exc_info=None
    )
    
    formatted = handler._format_message(record)
    assert '\\*bold\\*' in formatted

@pytest.mark.asyncio
async def test_send_with_retry_success(handler):
    """Test successful message sending."""
    # Mock the bot's send_message method
    future = asyncio.Future()
    future.set_result(None)
    handler.bot.send_message = MagicMock(return_value=future)
    
    handler._send_with_retry('123456789', 'Test message')
    
    handler.bot.send_message.assert_called_once_with(
        chat_id='123456789',
        text='Test message',
        parse_mode='HTML'
    )

@pytest.mark.asyncio
async def test_send_with_retry_failure(handler):
    """Test message sending with retries on failure."""
    # Mock the bot's send_message method to fail
    future = asyncio.Future()
    future.set_exception(TelegramError('Test error'))
    handler.bot.send_message = MagicMock(return_value=future)
    
    handler._send_with_retry('123456789', 'Test message')
    
    # Should retry max_retries times
    assert handler.bot.send_message.call_count == handler.max_retries + 1

def test_batching(handler):
    """Test message batching functionality."""
    # Mock the _send_with_retry method
    handler._send_with_retry = MagicMock()
    
    # Emit multiple messages
    records = [
        logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=i,
            msg=f'Test message {i}',
            args=(),
            exc_info=None
        )
        for i in range(3)
    ]
    
    for record in records:
        handler.emit(record)
    
    # Wait for batching
    import time
    time.sleep(handler.batch_interval * 2)
    
    # Should have made 2 calls (2 messages + 1 message)
    assert handler._send_with_retry.call_count == 2

def test_close(handler):
    """Test handler cleanup on close."""
    handler.close()
    assert handler.is_closed
    assert not handler.batch_thread.is_alive()

@pytest.mark.asyncio
async def test_multiple_chat_ids(mock_bot):
    """Test sending to multiple chat IDs."""
    handler = TelegramHandler(
        token='test_token',
        chat_ids=['123', '456'],
        batch_size=1
    )
    
    # Mock the _send_with_retry method
    handler._send_with_retry = MagicMock()
    
    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test message',
        args=(),
        exc_info=None
    )
    
    handler.emit(record)
    
    # Wait for batching
    import time
    time.sleep(handler.batch_interval * 2)
    
    # Should be called for each chat ID
    assert handler._send_with_retry.call_count == 2 