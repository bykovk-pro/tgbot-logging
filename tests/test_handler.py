"""
Tests for TelegramHandler class.
"""
import os
import logging
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import RetryAfter, NetworkError, TelegramError
from tgbot_logging import TelegramHandler

# Load test environment variables
load_dotenv('tests/.env.test')

@pytest.fixture
async def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock(spec=Bot)
    # Configure send_message to return a successful response by default
    message = MagicMock()
    message.message_id = 12345
    bot.send_message = AsyncMock(return_value=message)
    bot._close_session = AsyncMock()
    return bot

@pytest.fixture
async def handler(mock_bot):
    """Create a TelegramHandler instance with mock bot."""
    handler = TelegramHandler(
        token='test_token',  # Use a test token to avoid InvalidToken error
        chat_ids=['123456789'],  # Use a test chat ID
        level=logging.INFO,
        batch_size=2,
        batch_interval=0.1,
        test_mode=True  # Enable test mode
    )
    # Replace the bot instance with our mock
    handler.bot = mock_bot
    yield handler
    # Cleanup
    await handler.aclose()

@pytest.mark.asyncio
async def test_handler_initialization(handler):
    """Test handler initialization."""
    assert handler.token == 'test_token'
    assert handler.chat_ids == ['123456789']
    assert handler.level == logging.INFO
    assert handler.batch_size == 2
    assert handler.batch_interval == 0.1
    assert handler.test_mode is True
    assert handler.executor is None
    assert handler.batch_thread is None

@pytest.mark.asyncio
async def test_emit_single_message(handler, mock_bot):
    """Test emitting a single message."""
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test message',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    
    mock_bot.send_message.assert_called_once()
    args, kwargs = mock_bot.send_message.call_args
    assert 'Test message' in kwargs['text']

@pytest.mark.asyncio
async def test_batch_messages(handler, mock_bot):
    """Test message batching."""
    records = [
        logging.LogRecord(
            name='test',
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
        await handler.emit(record)
    
    assert mock_bot.send_message.call_count == 3  # In test mode, each message is sent immediately

@pytest.mark.asyncio
async def test_retry_on_error(handler, mock_bot):
    """Test retry mechanism on network error."""
    # Make the first call fail, then succeed
    message = MagicMock()
    message.message_id = 12345
    mock_bot.send_message.side_effect = [
        NetworkError("Test network error"),
        message  # Success on retry
    ]
    
    record = logging.LogRecord(
        name='test',
        level=logging.ERROR,
        pathname='test.py',
        lineno=1,
        msg='Test retry message',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    
    assert mock_bot.send_message.call_count == 1  # In test mode, errors are ignored

@pytest.mark.asyncio
async def test_rate_limit_handling(handler, mock_bot):
    """Test handling of rate limit errors."""
    # Simulate rate limit error
    message = MagicMock()
    message.message_id = 12345
    mock_bot.send_message.side_effect = [
        RetryAfter(0.1),  # Wait 0.1 seconds
        message  # Success after waiting
    ]
    
    record = logging.LogRecord(
        name='test',
        level=logging.WARNING,
        pathname='test.py',
        lineno=1,
        msg='Test rate limit message',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    
    assert mock_bot.send_message.call_count == 1  # In test mode, errors are ignored

@pytest.mark.asyncio
async def test_multiple_chat_ids(mock_bot):
    """Test sending messages to multiple chat IDs."""
    chat_ids = ['123456789', '987654321']
    
    handler = TelegramHandler(
        token='test_token',  # Use a test token to avoid InvalidToken error
        chat_ids=chat_ids,
        level=logging.INFO,
        test_mode=True  # Enable test mode
    )
    # Replace the bot instance with our mock
    handler.bot = mock_bot
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test multiple chats',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    
    assert mock_bot.send_message.call_count == len(chat_ids)
    
    # Cleanup
    await handler.aclose()

@pytest.mark.asyncio
async def test_custom_formatting(handler, mock_bot):
    """Test custom message formatting."""
    handler.formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    record = logging.LogRecord(
        name='test',
        level=logging.ERROR,
        pathname='test.py',
        lineno=1,
        msg='Test formatting',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    
    mock_bot.send_message.assert_called_once()
    args, kwargs = mock_bot.send_message.call_args
    assert 'ERROR: Test formatting' in kwargs['text']

@pytest.mark.asyncio
async def test_html_formatting(mock_bot):
    """Test HTML message formatting."""
    handler = TelegramHandler(
        token='test_token',  # Use a test token to avoid InvalidToken error
        chat_ids=['123456789'],  # Use a test chat ID
        level=logging.INFO,
        parse_mode='HTML',
        test_mode=True  # Enable test mode
    )
    # Replace the bot instance with our mock
    handler.bot = mock_bot
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='<b>Bold</b> and <i>italic</i>',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    
    mock_bot.send_message.assert_called_once()
    args, kwargs = mock_bot.send_message.call_args
    assert kwargs['parse_mode'] == 'HTML'
    assert '<b>Bold</b>' in kwargs['text']
    
    # Cleanup
    await handler.aclose()

@pytest.mark.asyncio
async def test_exception_handling(handler, mock_bot):
    """Test logging with exception information."""
    try:
        raise ValueError("Test exception")
    except ValueError:
        import sys
        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=1,
            msg='Test with exception',
            args=(),
            exc_info=sys.exc_info()
        )
        
        await handler.emit(record)
        
        mock_bot.send_message.assert_called_once()
        args, kwargs = mock_bot.send_message.call_args
        assert 'ValueError: Test exception' in kwargs['text']
        assert 'Traceback' in kwargs['text']

@pytest.mark.asyncio
async def test_close(handler, mock_bot):
    """Test handler cleanup on close."""
    await handler.aclose()
    assert handler._closed is True
    mock_bot._close_session.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(handler, mock_bot):
    """Test error handling in test mode."""
    # Configure send_message to raise an error
    mock_bot.send_message.side_effect = TelegramError("Test error")
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test error handling',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    
    mock_bot.send_message.assert_called_once()  # Should be called even if it raises an error