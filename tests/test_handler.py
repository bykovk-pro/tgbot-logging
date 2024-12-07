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
from telegram.error import RetryAfter, NetworkError, TelegramError, TimedOut, InvalidToken
from tgbot_logging import TelegramHandler
import sys

# Load test environment variables
load_dotenv('tests/.env.test')

# Test data
TEST_TOKEN = "test_token"
TEST_CHAT_ID = "123456789"
TEST_MESSAGE = "Test message"

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
    handler._bot = mock_bot
    yield handler
    # Cleanup
    await handler.close()

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
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
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
    await asyncio.sleep(0.2)  # Wait for messages to be processed
    
    assert mock_bot.send_message.call_count >= 1  # Messages should be batched

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
    await asyncio.sleep(0.2)  # Wait for retries
    
    assert mock_bot.send_message.call_count >= 1

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
    await asyncio.sleep(0.2)  # Wait for rate limit
    
    assert mock_bot.send_message.call_count >= 1

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
    handler._bot = mock_bot
    
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
    await asyncio.sleep(0.2)  # Wait for messages to be sent
    
    assert mock_bot.send_message.call_count >= len(chat_ids)
    
    # Cleanup
    await handler.close()

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
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
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
    handler._bot = mock_bot
    
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
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    assert kwargs['parse_mode'] == 'HTML'
    assert '<b>Bold</b>' in kwargs['text']
    
    # Cleanup
    await handler.close()

@pytest.mark.asyncio
async def test_exception_handling(handler, mock_bot):
    """Test logging with exception information."""
    try:
        raise ValueError("Test exception")
    except ValueError:
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
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    assert 'Test with exception' in kwargs['text']
    assert 'Traceback' in kwargs['text']
    assert 'ValueError' in kwargs['text']

@pytest.mark.asyncio
async def test_close(handler, mock_bot):
    """Test handler cleanup on close."""
    await handler.close()
    assert handler._closed is True
    mock_bot.close.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(handler, mock_bot):
    """Test various error handling scenarios."""
    # Test timeout error
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
    await asyncio.sleep(0.2)  # Wait for error handling
    
    assert mock_bot.send_message.called

@pytest.mark.asyncio
async def test_message_formatting_options(handler, mock_bot):
    """Test different message formatting options."""
    handler.project_name = "TestProject"
    handler.project_emoji = "🧪"
    handler.include_project_name = True
    handler.include_level_emoji = True
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test formatting options',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    assert "TestProject" in kwargs['text']
    assert "🧪" in kwargs['text']

@pytest.mark.asyncio
async def test_custom_level_emojis(handler, mock_bot):
    """Test custom level emojis."""
    handler.level_emojis = {
        logging.INFO: "ℹ️",
        logging.ERROR: "❌"
    }
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test custom emojis',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    assert "ℹ️" in kwargs['text']

@pytest.mark.asyncio
async def test_batch_flush_on_close(handler, mock_bot):
    """Test that pending messages are flushed on close."""
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
    
    await handler.close()
    await asyncio.sleep(0.2)  # Wait for flush
    
    assert mock_bot.send_message.called

@pytest.mark.asyncio
async def test_invalid_token_handling(mock_bot):
    """Test handling of invalid token."""
    handler = TelegramHandler(
        token="invalid_token",
        chat_ids=['123456789'],
        test_mode=True
    )
    handler._bot = mock_bot
    mock_bot.send_message.side_effect = NetworkError("Invalid token")
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test invalid token',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for error handling
    
    assert mock_bot.send_message.called
    await handler.close()

@pytest.mark.asyncio
async def test_invalid_chat_id_handling(mock_bot):
    """Test handling of invalid chat ID."""
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids="invalid_chat_id",
        test_mode=True
    )
    handler._bot = mock_bot
    mock_bot.send_message.side_effect = NetworkError("Chat not found")
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test invalid chat ID',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for error handling
    
    assert mock_bot.send_message.called
    await handler.close()

@pytest.mark.asyncio
async def test_long_message_handling(handler, mock_bot):
    """Test handling of long messages that exceed Telegram's limit."""
    long_message = "x" * 5000  # Create a message longer than 4096 characters
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg=long_message,
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message splitting
    
    assert mock_bot.send_message.call_count > 1  # Message should be split into multiple parts

@pytest.mark.asyncio
async def test_markdown_formatting(handler, mock_bot):
    """Test MarkdownV2 message formatting."""
    handler.parse_mode = 'MarkdownV2'
    handler.fmt = '*%(levelname)s*: %(message)s'
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test *bold* _italic_',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    assert kwargs['parse_mode'] == 'MarkdownV2'
    # Check that special characters are escaped
    text = kwargs['text']
    assert '\\*' in text  # Escaped asterisk
    assert '\\_' in text  # Escaped underscore

@pytest.mark.asyncio
async def test_custom_time_format(handler, mock_bot):
    """Test custom time format."""
    handler.datefmt = '%Y-%m-%d %H:%M:%S'
    handler.fmt = '[%(asctime)s] %(message)s'
    handler.formatter = logging.Formatter(handler.fmt, datefmt=handler.datefmt)
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test time format',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    # Check that time format matches our pattern
    import re
    assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', kwargs['text'])

@pytest.mark.asyncio
async def test_message_split_at_newline(handler, mock_bot):
    """Test that long messages are split at newlines when possible."""
    # Create a message with newlines that's longer than the limit
    message = "x" * 2000 + "\n" + "y" * 2000 + "\n" + "z" * 2000
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg=message,
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message splitting
    
    assert mock_bot.send_message.call_count > 1
    # Check that splits happened at newlines
    calls = mock_bot.send_message.call_args_list
    
    # Extract text from each call
    messages = [call[1]['text'] for call in calls]
    
    # Check that each part is in some message
    assert any("x" * 2000 in msg for msg in messages)  # First chunk
    assert any("y" * 2000 in msg for msg in messages)  # Second chunk
    assert any("z" * 2000 in msg for msg in messages)  # Third chunk

@pytest.mark.asyncio
async def test_timeout_handling(handler, mock_bot):
    """Test handling of timeout errors."""
    # Configure mock to fail with timeout twice, then succeed
    message = MagicMock()
    message.message_id = 12345
    mock_bot.send_message.side_effect = [
        TimedOut(),
        TimedOut(),
        message  # Success on third try
    ]
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test timeout',
        args=(),
        exc_info=None
    )
    
    # Temporarily reduce retry delay for faster test
    handler.retry_delay = 0.1
    
    await handler.emit(record)
    await asyncio.sleep(0.5)  # Wait for retries
    
    # In test mode, we only try once
    assert mock_bot.send_message.call_count == 1

@pytest.mark.asyncio
async def test_normal_mode_initialization():
    """Test handler initialization in normal mode."""
    handler = None
    try:
        handler = TelegramHandler(
            token=TEST_TOKEN,
            chat_ids=[TEST_CHAT_ID],
            test_mode=False
        )
        
        assert handler.executor is not None
        assert handler.batch_thread is not None
        assert handler.batch_thread.is_alive()
    finally:
        if handler:
            handler._closed = True
            if handler.batch_thread:
                handler.batch_event.set()
                handler.batch_thread.join(timeout=1.0)
            if handler.executor:
                handler.loop.call_soon_threadsafe(handler.loop.stop)
                handler.executor.shutdown()

@pytest.mark.asyncio
async def test_custom_message_format(handler, mock_bot):
    """Test custom message format function."""
    def custom_format(record, context):
        return f"CUSTOM: {record.getMessage()}"
    
    handler.message_format = custom_format
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test custom format',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    assert kwargs['text'].startswith('CUSTOM:')

@pytest.mark.asyncio
async def test_initialization_with_defaults():
    """Test handler initialization with default values."""
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID
    )
    try:
        assert handler.parse_mode == 'HTML'
        assert handler.batch_size == 1
        assert handler.batch_interval == 1.0
        assert handler.max_retries == 3
        assert handler.retry_delay == 1.0
        assert handler.project_emoji == '🔷'
        assert handler.add_hashtags is True
        assert handler.message_format is None
        assert handler.level_emojis == TelegramHandler.DEFAULT_LEVEL_EMOJI
        assert handler.include_project_name is True
        assert handler.include_level_emoji is True
        assert handler.datefmt is None
        assert handler.test_mode is False
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_message_format_with_project_name(handler, mock_bot):
    """Test message formatting with project name."""
    handler.project_name = "TestProject"
    handler.include_project_name = True
    handler.include_level_emoji = False
    handler.add_hashtags = True
    
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
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    assert "TestProject" in kwargs['text']
    assert "#TestProject" in kwargs['text']
    assert "#info" in kwargs['text']

@pytest.mark.asyncio
async def test_message_split_with_long_line(handler, mock_bot):
    """Test message splitting with a long line without newlines."""
    # Create a message longer than the limit without newlines
    message = "x" * 5000
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Disable extra formatting for this test
    handler.include_project_name = False
    handler.include_level_emoji = False
    handler.add_hashtags = False
    handler.formatter = logging.Formatter('%(message)s')
    handler.parse_mode = None
    handler.message_format = lambda r, c: r.getMessage()  # Use raw message
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message splitting
    
    assert mock_bot.send_message.call_count > 1
    # Check that splits happened at max length
    calls = mock_bot.send_message.call_args_list
    messages = [call[1]['text'] for call in calls]
    
    # Each message (except possibly the last) should be close to max length
    for msg in messages[:-1]:
        assert len(msg) <= 4096
        assert len(msg) > 3000  # Should be close to max length
    
    # Check that all parts together make up the original message
    combined = ''.join(messages)
    assert message in combined  # Original message should be contained in the combined text

@pytest.mark.asyncio
async def test_network_error_handling(handler, mock_bot):
    """Test handling of network errors."""
    # Configure mock to fail with network error twice, then succeed
    message = MagicMock()
    message.message_id = 12345
    mock_bot.send_message.side_effect = [
        NetworkError("Connection failed"),
        NetworkError("Connection failed"),
        message  # Success on third try
    ]
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test network error',
        args=(),
        exc_info=None
    )
    
    # Temporarily reduce retry delay for faster test
    handler.retry_delay = 0.1
    
    await handler.emit(record)
    await asyncio.sleep(0.5)  # Wait for retries
    
    # In test mode, we only try once
    assert mock_bot.send_message.call_count == 1

@pytest.mark.asyncio
async def test_invalid_token_error_handling(handler, mock_bot):
    """Test handling of invalid token errors."""
    mock_bot.send_message.side_effect = InvalidToken()
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test invalid token',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for error handling
    
    assert mock_bot.send_message.call_count == 1

@pytest.mark.asyncio
async def test_close_with_error(handler, mock_bot):
    """Test handler cleanup when close fails."""
    mock_bot.close.side_effect = Exception("Close failed")
    
    await handler.close()
    assert handler._closed is True
    mock_bot.close.assert_called_once()

@pytest.mark.asyncio
async def test_batch_sender_error_handling(handler, mock_bot):
    """Test error handling in batch sender thread."""
    if handler.test_mode:
        pytest.skip("Test requires normal mode")
    
    # Configure mock to raise an error
    mock_bot.send_message.side_effect = Exception("Batch sender error")
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test batch error',
        args=(),
        exc_info=None
    )
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for batch processing
    
    # Should continue running despite error
    assert not handler._closed

@pytest.mark.asyncio
async def test_initialization_with_invalid_values():
    """Test handler initialization with invalid values."""
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        batch_size=-1,  # Should be set to 1
        batch_interval=-0.1,  # Should be set to 0.1
        max_retries=-1,  # Should be set to 0
        retry_delay=-0.1  # Should be set to 0.1
    )
    try:
        assert handler.batch_size == 1
        assert handler.batch_interval == 0.1
        assert handler.max_retries == 0
        assert handler.retry_delay == 0.1
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_message_format_with_custom_time_formatter(handler, mock_bot):
    """Test message formatting with custom time formatter."""
    handler.datefmt = '%Y-%m-%d %H:%M:%S'
    handler.time_formatter = logging.Formatter(datefmt=handler.datefmt)
    
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
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    # Check that time format matches our pattern
    import re
    assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', kwargs['text'])

@pytest.mark.asyncio
async def test_message_split_with_newlines(handler, mock_bot):
    """Test message splitting with newlines."""
    # Create a message with newlines that's longer than the limit
    message = ("x" * 4000 + "\n" +  # First chunk
              "y" * 4000 + "\n" +  # Second chunk
              "z" * 4000)          # Third chunk
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Disable extra formatting for this test
    handler.message_format = lambda r, c: r.getMessage()  # Use raw message
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message splitting
    
    assert mock_bot.send_message.call_count == 3
    # Check that splits happened at newlines
    calls = mock_bot.send_message.call_args_list
    assert "x" * 4000 in calls[0][1]['text']  # First chunk
    assert "y" * 4000 in calls[1][1]['text']  # Second chunk
    assert "z" * 4000 in calls[2][1]['text']  # Third chunk

@pytest.mark.asyncio
async def test_error_handling_in_normal_mode(mock_bot):
    """Test error handling in normal mode."""
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=False,
        batch_interval=0.1,
        retry_delay=0.1
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to fail with network error twice, then succeed
        message = MagicMock()
        message.message_id = 12345
        mock_bot.send_message.side_effect = [
            NetworkError("Connection failed"),
            NetworkError("Connection failed"),
            message  # Success on third try
        ]
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test network error',
            args=(),
            exc_info=None
        )
        
        await handler.emit(record)
        await asyncio.sleep(0.5)  # Wait for retries
        
        assert mock_bot.send_message.call_count >= 2  # Should retry in normal mode
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_batch_sender_with_empty_queue(handler, mock_bot):
    """Test batch sender with empty queue."""
    if handler.test_mode:
        pytest.skip("Test requires normal mode")
    
    # Wait for a batch interval
    await asyncio.sleep(handler.batch_interval * 2)
    
    # Should not send any messages
    mock_bot.send_message.assert_not_called()

@pytest.mark.asyncio
async def test_batch_sender_with_multiple_chat_ids(mock_bot):
    """Test batch sender with multiple chat IDs."""
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=['123456789', '987654321'],
        test_mode=False,
        batch_interval=0.1
    )
    handler._bot = mock_bot
    
    try:
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
        await asyncio.sleep(0.2)  # Wait for batch processing
        
        assert mock_bot.send_message.call_count == 2  # Should send to both chats
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_batch_sender_with_error(mock_bot, capsys):
    """Test batch sender error handling."""
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=False,
        batch_interval=0.1,
        retry_delay=0.1,
        max_retries=2
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to fail with network error
        mock_bot.send_message.side_effect = NetworkError("Connection failed")
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test batch error',
            args=(),
            exc_info=None
        )
        
        await handler.emit(record)
        await asyncio.sleep(0.5)  # Wait for batch processing and retries
        
        # Should try to send at least once
        assert mock_bot.send_message.call_count >= 1
        
        # Error should be printed
        output = capsys.readouterr().out
        assert "Failed to send log to Telegram chat" in output
        assert "Connection failed" in output
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_message_format_with_custom_context(handler, mock_bot):
    """Test message formatting with custom context."""
    handler.datefmt = '%Y-%m-%d %H:%M:%S'
    handler.time_formatter = logging.Formatter(datefmt=handler.datefmt)
    handler.project_name = "TestProject"
    handler.include_project_name = True
    handler.include_level_emoji = True
    handler.add_hashtags = True
    
    def custom_format(record, context):
        parts = []
        if context['project_name']:
            parts.append(f"{context['project_emoji']} [{context['project_name']}]")
        if context['level_emojis']:
            parts.append(context['level_emojis'].get(record.levelno, '🔵'))
        parts.append(f"[{record.levelname}]")
        parts.append(f"[{context['format_time']()}]")
        parts.append(record.getMessage())
        return ' '.join(parts)
    
    handler.message_format = custom_format
    
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
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    assert "TestProject" in kwargs['text']
    assert "🔷" in kwargs['text']
    assert "ℹ️" in kwargs['text']
    assert "Test message" in kwargs['text']

@pytest.mark.asyncio
async def test_message_split_with_long_line_no_newlines(handler, mock_bot):
    """Test message splitting with a long line without newlines."""
    # Create a message longer than the limit without newlines
    message = "x" * 4096 + "y" * 4096  # Two chunks
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Disable extra formatting for this test
    handler.message_format = lambda r, c: r.getMessage()  # Use raw message
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message splitting
    
    assert mock_bot.send_message.call_count == 2
    # Check that splits happened at max length
    calls = mock_bot.send_message.call_args_list
    assert "x" * 4096 in calls[0][1]['text']  # First chunk
    assert "y" * 4096 in calls[1][1]['text']  # Second chunk

@pytest.mark.asyncio
async def test_error_handling_with_retries(mock_bot):
    """Test error handling with retries."""
    # Create handler in normal mode
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=False,
        batch_interval=0.1,
        retry_delay=0.1,
        max_retries=2
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to fail with network error twice, then succeed
        message = MagicMock()
        message.message_id = 12345
        mock_bot.send_message.side_effect = [
            NetworkError("Connection failed"),
            NetworkError("Connection failed"),
            message  # Success on third try
        ]
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test network error',
            args=(),
            exc_info=None
        )
        
        await handler.emit(record)
        await asyncio.sleep(0.5)  # Wait for retries
        
        assert mock_bot.send_message.call_count >= 2  # Should retry in normal mode
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_error_handling_with_rate_limit(mock_bot):
    """Test error handling with rate limit."""
    # Create handler in normal mode
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=False,
        batch_interval=0.1,
        retry_delay=0.1,
        max_retries=2
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to fail with rate limit, then succeed
        message = MagicMock()
        message.message_id = 12345
        mock_bot.send_message.side_effect = [
            RetryAfter(0.1),  # First try: rate limit
            message  # Success after waiting
        ]
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test rate limit',
            args=(),
            exc_info=None
        )
        
        await handler.emit(record)
        await asyncio.sleep(0.3)  # Wait for rate limit and retry
        
        assert mock_bot.send_message.call_count >= 2  # Should retry after rate limit
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_initialization_with_custom_formatter():
    """Test handler initialization with custom formatter."""
    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        fmt=fmt,
        datefmt=datefmt
    )
    try:
        assert isinstance(handler.formatter, logging.Formatter)
        assert handler.formatter._fmt == fmt
        assert handler.formatter.datefmt == datefmt
        assert isinstance(handler.time_formatter, logging.Formatter)
        assert handler.time_formatter.datefmt == datefmt
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_message_format_with_custom_time_format(handler, mock_bot):
    """Test message formatting with custom time format."""
    handler.datefmt = '%Y-%m-%d %H:%M:%S'
    handler.time_formatter = logging.Formatter(datefmt=handler.datefmt)
    handler.project_name = "TestProject"
    handler.include_project_name = True
    handler.include_level_emoji = True
    handler.add_hashtags = True
    
    def custom_format(record, context):
        parts = []
        if context['project_name']:
            parts.append(f"{context['project_emoji']} [{context['project_name']}]")
        if context['level_emojis']:
            parts.append(context['level_emojis'].get(record.levelno, '🔵'))
        parts.append(f"[{record.levelname}]")
        # Use time formatter from context
        parts.append(f"[{context['time_formatter'].formatTime(record)}]")
        parts.append(record.getMessage())
        return ' '.join(parts)
    
    handler.message_format = custom_format
    
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
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    # Check that time format matches our pattern
    import re
    assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', kwargs['text'])

@pytest.mark.asyncio
async def test_message_format_with_custom_formatter(handler, mock_bot):
    """Test message formatting with custom formatter."""
    handler.formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.project_name = "TestProject"
    handler.include_project_name = True
    handler.include_level_emoji = True
    handler.add_hashtags = True
    
    def custom_format(record, context):
        parts = []
        if context['project_name']:
            parts.append(f"{context['project_emoji']} [{context['project_name']}]")
        if context['level_emojis']:
            parts.append(context['level_emojis'].get(record.levelno, '🔵'))
        # Use formatter from context
        parts.append(context['formatter'].format(record))
        return ' '.join(parts)
    
    handler.message_format = custom_format
    
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
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    assert "INFO - Test message" in kwargs['text']

@pytest.mark.asyncio
async def test_message_format_with_custom_context_and_time(handler, mock_bot):
    """Test message formatting with custom context and time."""
    handler.datefmt = '%Y-%m-%d %H:%M:%S'
    handler.time_formatter = logging.Formatter(datefmt=handler.datefmt)
    handler.project_name = "TestProject"
    handler.include_project_name = True
    handler.include_level_emoji = True
    handler.add_hashtags = True
    
    def custom_format(record, context):
        parts = []
        if context['project_name']:
            parts.append(f"{context['project_emoji']} [{context['project_name']}]")
        if context['level_emojis']:
            parts.append(context['level_emojis'].get(record.levelno, '🔵'))
        parts.append(f"[{record.levelname}]")
        # Use format_time function from context
        parts.append(f"[{context['format_time']()}]")
        parts.append(record.getMessage())
        return ' '.join(parts)
    
    handler.message_format = custom_format
    
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
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    # Check that time format matches our pattern
    import re
    assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', kwargs['text'])

@pytest.mark.asyncio
async def test_message_split_with_long_line_and_newlines(handler, mock_bot):
    """Test message splitting with a long line and newlines."""
    # Create a message with newlines that's longer than the limit
    message = ("x" * 4000 + "\n" +  # First chunk
              "y" * 4000 + "\n" +  # Second chunk
              "z" * 4000 + "\n" +  # Third chunk
              "w" * 4000)          # Fourth chunk
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Disable extra formatting for this test
    handler.message_format = lambda r, c: r.getMessage()  # Use raw message
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message splitting
    
    assert mock_bot.send_message.call_count == 4
    # Check that splits happened at newlines and max length
    calls = mock_bot.send_message.call_args_list
    assert "x" * 4000 in calls[0][1]['text']  # First chunk
    assert "y" * 4000 in calls[1][1]['text']  # Second chunk
    assert "z" * 4000 in calls[2][1]['text']  # Third chunk
    assert "w" * 4000 in calls[3][1]['text']  # Fourth chunk

@pytest.mark.asyncio
async def test_error_handling_with_max_retries(mock_bot):
    """Test error handling with max retries."""
    # Create handler in normal mode
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=False,
        batch_interval=0.1,
        retry_delay=0.1,
        max_retries=2
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to always fail with network error
        mock_bot.send_message.side_effect = NetworkError("Connection failed")
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test max retries',
            args=(),
            exc_info=None
        )
        
        await handler.emit(record)
        await asyncio.sleep(0.5)  # Wait for retries
        
        # Should try exactly max_retries + 1 times (initial try + retries)
        assert mock_bot.send_message.call_count == handler.max_retries + 1
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_error_handling_with_rate_limit_and_error(mock_bot):
    """Test error handling with rate limit followed by error."""
    # Create handler in normal mode
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=False,
        batch_interval=0.1,
        retry_delay=0.1,
        max_retries=2
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to fail with rate limit, then network error, then succeed
        message = MagicMock()
        message.message_id = 12345
        mock_bot.send_message.side_effect = [
            RetryAfter(0.1),  # First try: rate limit
            NetworkError("Connection failed"),  # Second try: network error
            message  # Finally succeed
        ]
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test rate limit and error',
            args=(),
            exc_info=None
        )
        
        await handler.emit(record)
        await asyncio.sleep(0.3)  # Wait for rate limit and retry
        
        # Should try three times (rate limit + network error + success)
        assert mock_bot.send_message.call_count == 3
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_error_handling_with_multiple_rate_limits(mock_bot):
    """Test error handling with multiple rate limits."""
    # Create handler in normal mode
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=False,
        batch_interval=0.1,
        retry_delay=0.1,
        max_retries=2
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to fail with multiple rate limits, then succeed
        message = MagicMock()
        message.message_id = 12345
        mock_bot.send_message.side_effect = [
            RetryAfter(0.1),  # First try: rate limit
            RetryAfter(0.1),  # Second try: rate limit
            message  # Finally succeed
        ]
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test multiple rate limits',
            args=(),
            exc_info=None
        )
        
        await handler.emit(record)
        await asyncio.sleep(0.3)  # Wait for rate limit and retry
        
        # Should try three times (rate limit + rate limit + success)
        assert mock_bot.send_message.call_count == 3
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_error_handling_with_max_retries_and_rate_limit(mock_bot):
    """Test error handling with max retries and rate limit."""
    # Create handler in normal mode
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=False,
        batch_interval=0.1,
        retry_delay=0.1,
        max_retries=2
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to fail with rate limit, then network error until max retries
        mock_bot.send_message.side_effect = [
            RetryAfter(0.1),  # First try: rate limit
            NetworkError("Connection failed"),  # Second try: network error
            NetworkError("Connection failed")   # Third try: network error (exceeds max retries)
        ]
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test max retries with rate limit',
            args=(),
            exc_info=None
        )
        
        await handler.emit(record)
        await asyncio.sleep(0.3)  # Wait for retries
        
        # Should try three times (rate limit + initial try + retry)
        assert mock_bot.send_message.call_count == 3
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_message_format_with_custom_time_and_formatter(handler, mock_bot):
    """Test message formatting with custom time, formatter, and context."""
    handler.datefmt = '%Y-%m-%d %H:%M:%S'
    handler.time_formatter = logging.Formatter(datefmt=handler.datefmt)
    handler.formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.project_name = "TestProject"
    handler.include_project_name = True
    handler.include_level_emoji = True
    handler.add_hashtags = True
    
    def custom_format(record, context):
        parts = []
        if context['project_name']:
            parts.append(f"{context['project_emoji']} [{context['project_name']}]")
        if context['level_emojis']:
            parts.append(context['level_emojis'].get(record.levelno, '🔵'))
        # Use both time formatter and formatter from context
        parts.append(f"[{context['time_formatter'].formatTime(record)}]")
        parts.append(context['formatter'].format(record))
        # Use format_time function from context
        parts.append(f"[{context['format_time']()}]")
        return ' '.join(parts)
    
    handler.message_format = custom_format
    
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
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    # Check that time format matches our pattern
    import re
    assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', kwargs['text'])
    assert "INFO - Test message" in kwargs['text']
    # Check that time appears twice (from time_formatter and format_time)
    assert len(re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', kwargs['text'])) == 2

@pytest.mark.asyncio
async def test_message_split_with_long_line_and_newlines_and_max_length(handler, mock_bot):
    """Test message splitting with a long line, newlines, and max length."""
    # Create a message with newlines that's longer than the limit
    message = ("x" * 4096 + "\n" +  # First chunk (max length)
              "y" * 4096 + "\n" +  # Second chunk (max length)
              "z" * 4096 + "\n" +  # Third chunk (max length)
              "w" * 4096)          # Fourth chunk (max length)
    
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Disable extra formatting for this test
    handler.message_format = lambda r, c: r.getMessage()  # Use raw message
    
    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message splitting
    
    assert mock_bot.send_message.call_count == 4
    # Check that splits happened at max length
    calls = mock_bot.send_message.call_args_list
    for i, call in enumerate(calls):
        text = call[1]['text']
        assert len(text) == 4096  # Each chunk should be exactly max length
        if i == 0:
            assert text == "x" * 4096
        elif i == 1:
            assert text == "y" * 4096
        elif i == 2:
            assert text == "z" * 4096
        else:
            assert text == "w" * 4096

@pytest.mark.asyncio
async def test_error_handling_with_max_retries_and_rate_limit_and_error(mock_bot, capsys):
    """Test error handling with max retries, rate limit, and error."""
    # Create handler in normal mode
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=True,  # Use test mode to get error messages
        batch_interval=0.1,
        retry_delay=0.1,
        max_retries=2
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to fail with network error
        mock_bot.send_message.side_effect = NetworkError("Connection failed")
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test max retries with rate limit and error',
            args=(),
            exc_info=None
        )
        
        # Clear any previous output
        capsys.readouterr()
        
        await handler.emit(record)
        await asyncio.sleep(0.5)  # Wait for retries
        
        # Should try once in test mode
        assert mock_bot.send_message.call_count == 1
        
        # Check error message
        output = capsys.readouterr().out
        assert "Failed to send log to Telegram chat" in output
        assert "Connection failed" in output
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_error_handling_with_multiple_rate_limits_and_error(mock_bot, capsys):
    """Test error handling with multiple rate limits and error."""
    # Create handler in normal mode
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=False,
        batch_interval=0.1,
        retry_delay=0.1,
        max_retries=2
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to fail with multiple rate limits, then error
        mock_bot.send_message.side_effect = [
            RetryAfter(0.1),  # First try: rate limit
            RetryAfter(0.1),  # Second try: rate limit
            NetworkError("Connection failed"),  # Third try: network error
            NetworkError("Connection failed")   # Fourth try: network error (exceeds max retries)
        ]
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test multiple rate limits and error',
            args=(),
            exc_info=None
        )
        
        await handler.emit(record)
        await asyncio.sleep(0.5)  # Wait for retries
        
        # Should try three times (rate limits + initial try)
        assert mock_bot.send_message.call_count == 3
        
        # Check error message
        output = capsys.readouterr().out
        assert "Failed to send log to Telegram chat" in output
        assert "Connection failed" in output
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_error_handling_with_rate_limit_and_timeout(mock_bot):
    """Test error handling with rate limit and timeout."""
    # Create handler in normal mode
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=False,
        batch_interval=0.1,
        retry_delay=0.1,
        max_retries=2
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to fail with rate limit, then timeout, then succeed
        message = MagicMock()
        message.message_id = 12345
        mock_bot.send_message.side_effect = [
            RetryAfter(0.1),  # First try: rate limit
            TimedOut(),  # Second try: timeout
            message  # Finally succeed
        ]
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test rate limit and timeout',
            args=(),
            exc_info=None
        )
        
        await handler.emit(record)
        await asyncio.sleep(0.3)  # Wait for retries
        
        # Should try three times (rate limit + timeout + success)
        assert mock_bot.send_message.call_count == 3
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_message_format_with_custom_time_and_formatter_and_context(handler, mock_bot):
    """Test message formatting with custom time, formatter, and context."""
    handler.datefmt = '%Y-%m-%d %H:%M:%S'
    handler.time_formatter = logging.Formatter(datefmt=handler.datefmt)
    handler.formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.project_name = "TestProject"
    handler.include_project_name = True
    handler.include_level_emoji = True
    handler.add_hashtags = True
    
    def custom_format(record, context):
        parts = []
        if context['project_name']:
            parts.append(f"{context['project_emoji']} [{context['project_name']}]")
        if context['level_emojis']:
            parts.append(context['level_emojis'].get(record.levelno, '🔵'))
        # Use both time formatter and formatter from context
        parts.append(f"[{context['time_formatter'].formatTime(record)}]")
        parts.append(context['formatter'].format(record))
        # Use format_time function from context
        parts.append(f"[{context['format_time']()}]")
        return ' '.join(parts)
    
    handler.message_format = custom_format
    
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
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    # Check that time format matches our pattern
    import re
    assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', kwargs['text'])
    assert "INFO - Test message" in kwargs['text']
    # Check that time appears twice (from time_formatter and format_time)
    assert len(re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', kwargs['text'])) == 2

@pytest.mark.asyncio
async def test_error_handling_with_batch_retry_and_error(mock_bot):
    """Test error handling with batch retry and error."""
    # Create handler in normal mode
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=False,  # Use normal mode to test batch retry
        batch_interval=0.1,
        retry_delay=0.1,
        max_retries=2
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to fail with error, then succeed
        message = MagicMock()
        message.message_id = 12345
        mock_bot.send_message.side_effect = [
            TelegramError("Test error"),  # First try: error
            TelegramError("Test error"),  # Second try: error
            TelegramError("Test error")   # Third try: error (exceeds max retries)
        ]
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test batch retry',
            args=(),
            exc_info=None
        )
        
        await handler.emit(record)
        await asyncio.sleep(0.3)  # Wait for batch processing and retry
        
        # Should try max_retries + 1 times
        assert mock_bot.send_message.call_count == handler.max_retries + 1
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_message_format_with_custom_time_and_formatter_and_error_handling(handler, mock_bot):
    """Test message formatting with custom time, formatter, and error handling."""
    handler.datefmt = '%Y-%m-%d %H:%M:%S'
    handler.time_formatter = logging.Formatter(datefmt=handler.datefmt)
    handler.formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.project_name = "TestProject"
    handler.include_project_name = True
    handler.include_level_emoji = True
    handler.add_hashtags = True
    
    def custom_format(record, context):
        parts = []
        if context['project_name']:
            parts.append(f"{context['project_emoji']} [{context['project_name']}]")
        if context['level_emojis']:
            parts.append(context['level_emojis'].get(record.levelno, '🔵'))
        # Use both time formatter and formatter from context
        parts.append(f"[{context['time_formatter'].formatTime(record)}]")
        parts.append(context['formatter'].format(record))
        # Use format_time function from context
        parts.append(f"[{context['format_time']()}]")
        # Raise an error to test error handling
        raise ValueError("Test error")
    
    handler.message_format = custom_format
    
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
    await asyncio.sleep(0.2)  # Wait for message to be processed
    
    # Should not call send_message due to error
    mock_bot.send_message.assert_not_called()

@pytest.mark.asyncio
async def test_error_handling_with_batch_retry_and_error_and_timeout(mock_bot):
    """Test error handling with batch retry, error, and timeout."""
    # Create handler in normal mode
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=False,  # Use normal mode to test batch retry
        batch_interval=0.1,
        retry_delay=0.1,
        max_retries=2
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to fail with error, then timeout, then error
        message = MagicMock()
        message.message_id = 12345
        mock_bot.send_message.side_effect = [
            TelegramError("Test error"),  # First try: error
            TimedOut(),  # Second try: timeout
            TelegramError("Test error")   # Third try: error (exceeds max retries)
        ]
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test batch retry',
            args=(),
            exc_info=None
        )
        
        await handler.emit(record)
        await asyncio.sleep(0.3)  # Wait for batch processing and retry
        
        # Should try max_retries + 1 times
        assert mock_bot.send_message.call_count == handler.max_retries + 1
    finally:
        await handler.close()

@pytest.mark.asyncio
async def test_error_handling_with_batch_retry_and_error_and_rate_limit(mock_bot):
    """Test error handling with batch retry, error, and rate limit."""
    # Create handler in normal mode
    handler = TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=[TEST_CHAT_ID],
        test_mode=False,  # Use normal mode to test batch retry
        batch_interval=0.1,
        retry_delay=0.1,
        max_retries=2
    )
    handler._bot = mock_bot
    
    try:
        # Configure mock to fail with error, then rate limit, then error
        message = MagicMock()
        message.message_id = 12345
        mock_bot.send_message.side_effect = [
            TelegramError("Test error"),  # First try: error
            RetryAfter(0.1),  # Second try: rate limit
            TelegramError("Test error")   # Third try: error (exceeds max retries)
        ]
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test batch retry',
            args=(),
            exc_info=None
        )
        
        await handler.emit(record)
        await asyncio.sleep(0.3)  # Wait for batch processing and retry
        
        # Should try max_retries + 1 times
        assert mock_bot.send_message.call_count == handler.max_retries + 1
    finally:
        await handler.close()