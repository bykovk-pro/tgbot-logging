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
from telegram.error import (
    RetryAfter,
    NetworkError,
    TelegramError,
    TimedOut,
    InvalidToken,
)
from tgbot_logging import TelegramHandler
import sys
import signal
import time

# Load test environment variables
load_dotenv("tests/.env.test")

# Test data
TEST_TOKEN = "test_token"
TEST_CHAT_ID = "123456789"
TEST_MESSAGE = "Test message"
TEST_BATCH_SIZE = 5
TEST_BATCH_INTERVAL = 0.1


@pytest.fixture
async def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock(spec=Bot)
    # Configure send_message to return a successful response by default
    message = MagicMock()
    message.message_id = 12345
    bot.send_message = AsyncMock(return_value=message)
    bot.close = AsyncMock()
    return bot


@pytest.fixture
async def handler(mock_bot):
    """Create a TelegramHandler instance with mock bot."""
    handler = TelegramHandler(
        token="test_token",  # Use a test token to avoid InvalidToken error
        chat_ids=["123456789"],  # Use a test chat ID
        level=logging.INFO,
        batch_size=1,  # Use batch size 1 for single message tests
        batch_interval=TEST_BATCH_INTERVAL,
        test_mode=True,  # Enable test mode for fixtures
    )
    # Replace the bot instance with our mock
    handler._bot = mock_bot
    yield handler
    # Cleanup
    await handler.close()


@pytest.fixture
async def batch_handler(mock_bot):
    """Create a TelegramHandler instance with batching enabled."""
    handler = TelegramHandler(
        token="test_token",  # Use a test token to avoid InvalidToken error
        chat_ids=["123456789"],  # Use a test chat ID
        level=logging.INFO,
        batch_size=TEST_BATCH_SIZE,  # Use larger batch size for batch tests
        batch_interval=TEST_BATCH_INTERVAL,
        test_mode=True,  # Enable test mode for fixtures
    )
    # Replace the bot instance with our mock
    handler._bot = mock_bot
    yield handler
    # Cleanup
    await handler.close()


@pytest.mark.asyncio
async def test_handler_initialization(handler):
    """Test handler initialization."""
    assert handler.token == "test_token"
    assert handler.chat_ids == ["123456789"]
    assert handler.level == logging.INFO
    assert handler.batch_size == 1
    assert handler.batch_interval == TEST_BATCH_INTERVAL
    assert handler._is_shutting_down.is_set() is False
    assert handler._shutdown_complete.is_set() is False


@pytest.mark.asyncio
async def test_emit_single_message(handler, mock_bot):
    """Test emitting a single message."""
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message to be processed

    mock_bot.send_message.assert_called_once()
    args, kwargs = mock_bot.send_message.call_args
    assert "Test message" in kwargs["text"]


@pytest.mark.asyncio
async def test_batch_messages(batch_handler, mock_bot):
    """Test message batching."""
    records = [
        logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=i,
            msg=f"Test message {i}",
            args=(),
            exc_info=None,
        )
        for i in range(TEST_BATCH_SIZE)
    ]

    for record in records:
        await batch_handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for messages to be processed

    assert mock_bot.send_message.call_count >= 1  # Messages should be batched
    args, kwargs = mock_bot.send_message.call_args
    assert len(kwargs["text"].split("\n\n")) == TEST_BATCH_SIZE


@pytest.mark.asyncio
async def test_retry_on_error(handler, mock_bot):
    """Test retry mechanism on network error."""
    # Make the first call fail, then succeed
    message = MagicMock()
    message.message_id = 12345
    mock_bot.send_message.side_effect = [
        NetworkError("Test network error"),
        message,  # Success on retry
    ]

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="Test retry message",
        args=(),
        exc_info=None,
    )

    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for retries

    assert mock_bot.send_message.call_count >= 2  # Initial attempt + retry


@pytest.mark.asyncio
async def test_rate_limit_handling(handler, mock_bot):
    """Test handling of rate limit errors."""
    # Simulate rate limit error
    message = MagicMock()
    message.message_id = 12345
    mock_bot.send_message.side_effect = [
        RetryAfter(0.1),  # Wait 0.1 seconds
        message,  # Success after waiting
    ]

    record = logging.LogRecord(
        name="test",
        level=logging.WARNING,
        pathname="test.py",
        lineno=1,
        msg="Test rate limit message",
        args=(),
        exc_info=None,
    )

    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for rate limit

    assert mock_bot.send_message.call_count >= 2  # Initial attempt + retry


@pytest.mark.asyncio
async def test_multiple_chat_ids(mock_bot):
    """Test sending messages to multiple chat IDs."""
    chat_ids = ["123456789", "987654321"]

    handler = TelegramHandler(
        token="test_token",  # Use a test token to avoid InvalidToken error
        chat_ids=chat_ids,
        level=logging.INFO,
        batch_size=1,  # Use batch size 1 for immediate sending
        test_mode=True,  # Enable test mode
    )
    handler._bot = mock_bot

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test multiple chats",
        args=(),
        exc_info=None,
    )

    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for messages to be sent

    assert mock_bot.send_message.call_count >= len(chat_ids)

    # Cleanup
    await handler.close()


@pytest.mark.asyncio
async def test_custom_formatting(handler, mock_bot):
    """Test custom message formatting."""
    handler.formatter = logging.Formatter("%(levelname)s: %(message)s")

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="Test formatting",
        args=(),
        exc_info=None,
    )

    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message to be processed

    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    assert "ERROR: Test formatting" in kwargs["text"]


@pytest.mark.asyncio
async def test_html_formatting(mock_bot):
    """Test HTML message formatting."""
    handler = TelegramHandler(
        token="test_token",  # Use a test token to avoid InvalidToken error
        chat_ids=["123456789"],  # Use a test chat ID
        level=logging.INFO,
        parse_mode="HTML",
        batch_size=1,  # Use batch size 1 for immediate sending
        test_mode=True,  # Enable test mode
    )
    handler._bot = mock_bot

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="<b>Bold</b> and <i>italic</i>",
        args=(),
        exc_info=None,
    )

    await handler.emit(record)
    await asyncio.sleep(0.2)  # Wait for message to be processed

    mock_bot.send_message.assert_called()
    args, kwargs = mock_bot.send_message.call_args
    assert kwargs["parse_mode"] == "HTML"
    assert "<b>Bold</b>" in kwargs["text"]

    # Cleanup
    await handler.close()


@pytest.mark.asyncio
async def test_graceful_shutdown(batch_handler, mock_bot):
    """Test graceful shutdown."""
    # Add some messages
    records = [
        logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=i,
            msg=f"Test message {i}",
            args=(),
            exc_info=None,
        )
        for i in range(TEST_BATCH_SIZE - 1)  # Add messages just under batch size
    ]

    for record in records:
        await batch_handler.emit(record)

    # Trigger shutdown
    await batch_handler.close()

    # Check that all messages were sent
    assert mock_bot.send_message.call_count >= 1
    assert mock_bot.close.call_count == 1
    assert batch_handler._closed
    assert batch_handler._is_shutting_down.is_set()


@pytest.mark.asyncio
async def test_signal_handling(handler, mock_bot):
    """Test signal handling."""
    # Add a message
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    await handler.emit(record)

    # Simulate SIGTERM
    with patch("signal.signal") as mock_signal:
        handler._setup_signal_handlers()
        # Get the signal handler
        signal_handler = mock_signal.call_args_list[0][0][1]
        # Call it with SIGTERM
        signal_handler(signal.SIGTERM, None)

        # Wait for shutdown
        await asyncio.sleep(0.2)

        # Check shutdown was initiated
        assert handler._is_shutting_down.is_set()
        assert mock_bot.send_message.called
        assert mock_bot.close.called


@pytest.mark.asyncio
async def test_error_handling_per_chat(handler, mock_bot):
    """Test error handling for each chat separately."""
    # Mock bot method to fail for one chat but succeed for another
    message = MagicMock()
    message.message_id = 12345

    # Create a counter to track calls
    call_count = 0

    async def mock_send_message(chat_id, **kwargs):
        nonlocal call_count
        call_count += 1
        if chat_id == "123":
            if call_count <= handler.max_retries:
                raise TimedOut()
            return message
        return message

    mock_bot.send_message = AsyncMock(side_effect=mock_send_message)
    handler.chat_ids = ["123", "456"]

    # Add message
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    await handler.emit(record)
    await asyncio.sleep(0.5)  # Wait for async processing and retries

    # Check that both chats were attempted
    assert call_count >= 2


@pytest.mark.asyncio
async def test_rate_limiting(handler, mock_bot):
    """Test rate limiting and retry mechanism."""
    # Mock bot method to simulate rate limiting
    calls = 0

    async def mock_send_message(**kwargs):
        nonlocal calls
        calls += 1
        if calls <= 2:  # First two calls hit rate limit
            raise RetryAfter(retry_after=0.1)
        return True

    mock_bot.send_message = AsyncMock(side_effect=mock_send_message)

    # Add message
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    await handler.emit(record)
    await asyncio.sleep(0.3)  # Wait for retries

    # Check retries
    assert calls >= 3  # Initial + 2 retries


@pytest.mark.asyncio
async def test_message_batching(batch_handler, mock_bot):
    """Test message batching mechanism."""
    # Add messages just under batch size
    for i in range(TEST_BATCH_SIZE - 1):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=f"Message {i}",
            args=(),
            exc_info=None,
        )
        await batch_handler.emit(record)

    # Check not sent yet
    assert mock_bot.send_message.call_count == 0

    # Add one more message to trigger batch
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Final message",
        args=(),
        exc_info=None,
    )
    await batch_handler.emit(record)

    # Wait for batch processing
    await asyncio.sleep(0.2)

    # Check batch was sent
    assert mock_bot.send_message.call_count == 1
    # Check message format
    call_args = mock_bot.send_message.call_args[1]
    assert len(call_args["text"].split("\n\n")) == TEST_BATCH_SIZE


@pytest.mark.asyncio
async def test_async_context_manager():
    """Test async context manager."""
    async with TelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        batch_size=1,  # Use batch size 1 for immediate sending
        test_mode=True,  # Enable test mode
    ) as handler:
        # Add a message
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        await handler.emit(record)

        # Check message was queued
        assert any(not q.empty() for q in handler.message_queue.values())

    # Check cleanup after context exit
    assert handler._closed
    assert handler._is_shutting_down.is_set()
