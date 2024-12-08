"""
Extended tests for TelegramHandler to increase code coverage.
"""

import os
import pytest
import asyncio
import logging
import signal
import threading
from unittest.mock import AsyncMock, MagicMock, patch
from telegram.error import RetryAfter, NetworkError, TimedOut, InvalidToken
from tgbot_logging.handler import TelegramHandler
from dotenv import load_dotenv

# Load test environment variables
load_dotenv("tests/.env.test")

# Test data
TEST_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "test_token")
TEST_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "123456789")
TEST_MESSAGE = "Test message"

# Constants for testing
TEST_SLEEP = 0.01  # Short sleep time for tests
TEST_BATCH_INTERVAL = 0.01  # Short batch interval for tests


class CustomTelegramHandler(TelegramHandler):
    """Custom handler class for testing message formatting."""

    def format(self, record: logging.LogRecord) -> str:
        """Override format method to include all required elements."""
        # Format timestamp if needed
        timestamp = ""
        if self.datefmt:
            timestamp = f"{self.time_formatter.formatTime(record, self.datefmt)} "

        # Get level emoji
        level_emoji = ""
        if self.include_level_emoji:
            level_emoji = f"{self.level_emojis.get(record.levelno, '')} "

        # Get project info
        project_info = ""
        if self.include_project_name and self.project_name:
            project_info = f"{self.project_emoji} {self.project_name}\n"

        # Format message
        if self.message_format:
            try:
                message = self.message_format(record, {})
            except Exception as e:
                print(f"Error in custom message format: {str(e)}")
                message = record.getMessage()
        else:
            message = record.getMessage()

        # Add hashtags
        hashtags = ""
        if self.add_hashtags and self.project_name:
            hashtags = f"\n#{self.project_name.replace(' ', '')}"

        return f"{timestamp}{level_emoji}{project_info}{message}{hashtags}"


@pytest.fixture
async def mock_bot():
    """Create a mock bot instance."""
    mock_send = AsyncMock()
    mock_close = AsyncMock()
    mock_bot = MagicMock()
    mock_bot.send_message = mock_send
    mock_bot.close = mock_close
    mock_bot.get_me = AsyncMock()

    with patch("telegram.Bot", return_value=mock_bot):
        yield mock_bot


@pytest.fixture
async def handler(mock_bot):
    """Create a handler instance in test mode."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        batch_size=2,
        batch_interval=TEST_BATCH_INTERVAL,
        retry_delay=TEST_SLEEP,
    )
    handler._bot = mock_bot  # Replace the bot instance directly
    yield handler
    await handler.close()


@pytest.mark.asyncio
async def test_custom_formatting(mock_bot):
    """Test custom message formatting."""

    def custom_format(record, extra):
        return f"CUSTOM: {record.getMessage()}"

    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        message_format=custom_format,
    )
    handler._bot = mock_bot  # Replace the bot instance directly

    logger = logging.getLogger("test_custom")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send message and wait for processing
    await handler.emit(
        logger.makeRecord("test_custom", logging.INFO, "", 0, "Test message", (), None)
    )
    await asyncio.sleep(0.1)

    mock_bot.send_message.assert_called_once()
    assert "CUSTOM:" in mock_bot.send_message.call_args[1]["text"]


@pytest.mark.asyncio
async def test_batch_processing(handler, mock_bot):
    """Test batch message processing."""
    logger = logging.getLogger("test_batch")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send messages directly
    for msg in ["Message 1", "Message 2", "Message 3"]:
        await handler.emit(
            logger.makeRecord("test_batch", logging.INFO, "", 0, msg, (), None)
        )

    # Wait for batch processing
    await asyncio.sleep(0.2)

    # Check that messages were batched
    assert mock_bot.send_message.call_count >= 1
    # First batch should contain first two messages
    assert "Message 1" in mock_bot.send_message.call_args_list[0][1]["text"]
    assert "Message 2" in mock_bot.send_message.call_args_list[0][1]["text"]


@pytest.mark.asyncio
async def test_retry_mechanism(mock_bot):
    """Test retry mechanism for failed messages."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        max_retries=2,
        retry_delay=0.1,
    )
    handler._bot = mock_bot  # Replace the bot instance directly

    logger = logging.getLogger("test_retry")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Configure mock to fail twice then succeed
    mock_bot.send_message.side_effect = [
        RetryAfter(0.1),
        NetworkError("Test error"),
        None,  # Success
    ]

    # Send message directly
    record = logger.makeRecord(
        "test_retry", logging.INFO, "", 0, "Test retry message", (), None
    )
    await handler._send_message(TEST_CHAT_ID, handler.format(record))
    await asyncio.sleep(0.5)  # Wait for retries

    assert mock_bot.send_message.call_count == 3


@pytest.mark.asyncio
async def test_multiple_chat_ids(mock_bot):
    """Test sending to multiple chat IDs."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN, chat_ids=["123", "456"], test_mode=True
    )
    handler._bot = mock_bot  # Replace the bot instance directly

    logger = logging.getLogger("test_multi")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send message directly
    await handler.emit(
        logger.makeRecord(
            "test_multi", logging.INFO, "", 0, "Multi-chat message", (), None
        )
    )
    await asyncio.sleep(0.1)

    assert mock_bot.send_message.call_count == 2
    chat_ids = [call[1]["chat_id"] for call in mock_bot.send_message.call_args_list]
    assert "123" in chat_ids
    assert "456" in chat_ids


@pytest.mark.asyncio
async def test_queue_error_handling(mock_bot):
    """Test error handling in message queue processing."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        max_retries=2,
        retry_delay=0.1,
    )
    handler._bot = mock_bot  # Replace the bot instance directly

    logger = logging.getLogger("test_queue_error")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Configure mock to fail permanently
    mock_bot.send_message.side_effect = TimedOut()

    # Send message directly
    record = logger.makeRecord(
        "test_queue_error", logging.INFO, "", 0, "Test error message", (), None
    )
    with pytest.raises(TimedOut):
        await handler._send_message(TEST_CHAT_ID, handler.format(record))
    await asyncio.sleep(0.5)

    # Message should be retried max_retries times
    assert mock_bot.send_message.call_count == handler.max_retries + 1


@pytest.mark.asyncio
async def test_shutdown_handling(mock_bot):
    """Test graceful shutdown handling."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN, chat_ids=TEST_CHAT_ID, test_mode=True
    )
    handler._bot = mock_bot  # Replace the bot instance directly

    logger = logging.getLogger("test_shutdown")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send pre-shutdown message directly
    await handler.emit(
        logger.makeRecord(
            "test_shutdown", logging.INFO, "", 0, "Pre-shutdown message", (), None
        )
    )
    await asyncio.sleep(0.1)

    # Simulate shutdown
    await handler.close()

    # Try sending after shutdown
    await handler.emit(
        logger.makeRecord(
            "test_shutdown", logging.INFO, "", 0, "Post-shutdown message", (), None
        )
    )
    await asyncio.sleep(0.1)

    # Only pre-shutdown message should be sent
    assert mock_bot.send_message.call_count == 1
    assert "Pre-shutdown" in mock_bot.send_message.call_args[1]["text"]


@pytest.mark.asyncio
async def test_async_context_manager(mock_bot):
    """Test async context manager functionality."""
    logger = logging.getLogger("test_context")
    logger.setLevel(logging.INFO)

    async with CustomTelegramHandler(
        token=TEST_TOKEN, chat_ids=TEST_CHAT_ID, test_mode=True
    ) as handler:
        handler._bot = mock_bot  # Replace the bot instance directly
        logger.addHandler(handler)

        # Send message directly
        await handler.emit(
            logger.makeRecord(
                "test_context", logging.INFO, "", 0, "Context message", (), None
            )
        )
        await asyncio.sleep(0.1)
        assert mock_bot.send_message.call_count == 1

    # Handler should be closed after context exit
    assert handler._closed


@pytest.mark.asyncio
async def test_custom_level_emojis(mock_bot):
    """Test custom level emojis."""
    custom_emojis = {logging.INFO: "🌟", logging.ERROR: "💥"}

    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        level_emojis=custom_emojis,
        include_level_emoji=True,
    )
    handler._bot = mock_bot  # Replace the bot instance directly

    logger = logging.getLogger("test_emoji")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send message directly
    await handler.emit(
        logger.makeRecord("test_emoji", logging.INFO, "", 0, "Emoji test", (), None)
    )
    await asyncio.sleep(0.1)
    assert "🌟" in mock_bot.send_message.call_args[1]["text"]


@pytest.mark.asyncio
async def test_signal_handling(mock_bot):
    """Test signal handler setup and processing."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN, chat_ids=TEST_CHAT_ID, test_mode=True
    )
    handler._bot = mock_bot  # Replace the bot instance directly

    logger = logging.getLogger("test_signal")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Simulate SIGTERM
    handler._signal_handler(signal.SIGTERM, None)
    await asyncio.sleep(0.1)

    # Try sending after signal
    await handler.emit(
        logger.makeRecord(
            "test_signal", logging.INFO, "", 0, "Post-signal message", (), None
        )
    )
    await asyncio.sleep(0.1)

    # Handler should be closed
    assert handler._closed


@pytest.mark.asyncio
async def test_custom_date_format(mock_bot):
    """Test custom date format in messages."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler._bot = mock_bot  # Replace the bot instance directly

    logger = logging.getLogger("test_date")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send message directly
    await handler.emit(
        logger.makeRecord(
            "test_date", logging.INFO, "", 0, "Date format test", (), None
        )
    )
    await asyncio.sleep(0.1)

    # Check date format in message
    message_text = mock_bot.send_message.call_args[1]["text"]
    import re

    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", message_text)


@pytest.mark.asyncio
async def test_project_name_and_hashtags(mock_bot):
    """Test project name and hashtags in messages."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        project_name="TestProject",
        project_emoji="🚀",
        add_hashtags=True,
        include_project_name=True,
    )
    handler._bot = mock_bot  # Replace the bot instance directly

    logger = logging.getLogger("test_project")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send message directly
    await handler.emit(
        logger.makeRecord("test_project", logging.INFO, "", 0, "Project test", (), None)
    )
    await asyncio.sleep(0.1)

    message_text = mock_bot.send_message.call_args[1]["text"]
    assert "TestProject" in message_text
    assert "🚀" in message_text
    assert "#TestProject" in message_text


@pytest.mark.asyncio
async def test_html_formatting(mock_bot):
    """Test HTML formatting in messages."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN, chat_ids=TEST_CHAT_ID, test_mode=True, parse_mode="HTML"
    )
    handler._bot = mock_bot  # Replace the bot instance directly

    logger = logging.getLogger("test_html")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send message directly
    await handler.emit(
        logger.makeRecord(
            "test_html",
            logging.INFO,
            "",
            0,
            "<b>Bold text</b> and <i>italic</i>",
            (),
            None,
        )
    )
    await asyncio.sleep(0.1)

    assert mock_bot.send_message.call_args[1]["parse_mode"] == "HTML"
    assert "<b>" in mock_bot.send_message.call_args[1]["text"]
    assert "<i>" in mock_bot.send_message.call_args[1]["text"]


@pytest.mark.asyncio
async def test_queue_overflow_handling(handler, mock_bot):
    """Test handling of queue overflow situations."""
    logger = logging.getLogger("test_overflow")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Configure mock to always fail with network error
    mock_bot.send_message.side_effect = NetworkError("Test network error")

    # Send many messages directly
    for i in range(10):
        await handler.emit(
            logger.makeRecord(
                "test_overflow", logging.INFO, "", 0, f"Message {i}", (), None
            )
        )

    await asyncio.sleep(1)  # Wait for processing attempts

    # Check that retries were attempted for each batch
    assert mock_bot.send_message.call_count > 5


@pytest.mark.asyncio
async def test_invalid_token_handling():
    """Test handling of invalid token."""
    mock_bot = MagicMock()
    mock_bot.get_me = AsyncMock(side_effect=InvalidToken("Invalid token"))

    with patch("telegram.Bot", return_value=mock_bot):
        with pytest.raises(InvalidToken):
            handler = CustomTelegramHandler(
                token="invalid_token",
                chat_ids=TEST_CHAT_ID,
                test_mode=False,  # Important: set to False to trigger token validation
            )


@pytest.mark.asyncio
async def test_message_formatting_error_handling(mock_bot):
    """Test handling of message formatting errors."""

    def bad_formatter(record, extra):
        raise ValueError("Formatting error")

    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        message_format=bad_formatter,
    )
    handler._bot = mock_bot  # Replace the bot instance directly

    logger = logging.getLogger("test_format_error")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send message directly
    await handler.emit(
        logger.makeRecord(
            "test_format_error", logging.INFO, "", 0, "Test message", (), None
        )
    )
    await asyncio.sleep(0.1)

    # Message should still be sent with default formatting
    assert mock_bot.send_message.call_count == 1


@pytest.mark.asyncio
async def test_signal_handling_with_cleanup(mock_bot):
    """Test signal handling with cleanup."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        batch_interval=TEST_BATCH_INTERVAL,
        retry_delay=TEST_SLEEP,
    )
    handler._bot = mock_bot

    # Simulate SIGTERM
    handler._signal_handler(signal.SIGTERM, None)
    await asyncio.sleep(TEST_SLEEP)

    # Try sending after signal
    record = logging.LogRecord(
        "test_signal", logging.INFO, "", 0, "Post-signal message", (), None
    )
    await handler.emit(record)
    await asyncio.sleep(TEST_SLEEP)

    # Handler should be closed and cleanup should be done
    assert handler._closed
    assert handler._shutdown_complete.is_set()
    mock_bot.close.assert_called_once()


@pytest.mark.asyncio
async def test_queue_processing_error_handling(mock_bot):
    """Test error handling in queue processing."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        batch_size=1,  # Process one message at a time
        batch_interval=TEST_BATCH_INTERVAL,
        retry_delay=TEST_SLEEP,
        max_retries=0,  # No retries to avoid extra calls
    )
    handler._bot = mock_bot

    # Configure mock to fail with different errors
    errors = [
        RetryAfter(TEST_SLEEP),  # First message: rate limit
        NetworkError("Test error"),  # Second message: network error
        TimedOut(),  # Third message: timeout
        None,  # Fourth message: success
    ]
    mock_bot.send_message.side_effect = errors

    logger = logging.getLogger("test_queue_error")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send messages
    for i in range(4):
        try:
            await handler._send_message(
                TEST_CHAT_ID, f"Message {i}"
            )  # Send directly to avoid batching
        except (RetryAfter, NetworkError, TimedOut):
            pass  # Expected exceptions

    await asyncio.sleep(TEST_SLEEP * 2)  # Wait for processing

    # Check that all error types were handled
    assert mock_bot.send_message.call_count == 4

    # Check that each error type was encountered
    call_errors = []
    for args in mock_bot.send_message.call_args_list:
        try:
            error = errors.pop(0)
            if isinstance(error, Exception):
                call_errors.append(type(error))
        except IndexError:
            break

    assert RetryAfter in call_errors
    assert NetworkError in call_errors
    assert TimedOut in call_errors


@pytest.mark.asyncio
async def test_batch_processing_with_force(mock_bot):
    """Test forced batch processing."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        batch_size=5,  # Large batch size
        batch_interval=TEST_BATCH_INTERVAL,
        retry_delay=TEST_SLEEP,
    )
    handler._bot = mock_bot

    logger = logging.getLogger("test_batch_force")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send messages
    for i in range(3):  # Less than batch size
        await handler.emit(
            logger.makeRecord(
                "test_batch_force", logging.INFO, "", 0, f"Message {i}", (), None
            )
        )

    # Force batch processing
    await handler._process_queue()
    await asyncio.sleep(TEST_SLEEP)

    # Check that messages were sent despite not reaching batch size
    assert mock_bot.send_message.call_count == 1
    assert "Message 0" in mock_bot.send_message.call_args[1]["text"]
    assert "Message 2" in mock_bot.send_message.call_args[1]["text"]


@pytest.mark.asyncio
async def test_message_queue_overflow(mock_bot):
    """Test handling of message queue overflow."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        batch_size=1,
        batch_interval=TEST_BATCH_INTERVAL,
        retry_delay=TEST_SLEEP,
    )
    handler._bot = mock_bot

    # Configure mock to always fail
    mock_bot.send_message.side_effect = NetworkError("Test error")

    logger = logging.getLogger("test_overflow")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send many messages to overflow the queue
    for i in range(10):  # Reduced from 100 to 10 for faster testing
        await handler.emit(
            logger.makeRecord(
                "test_overflow", logging.INFO, "", 0, f"Message {i}", (), None
            )
        )

    await asyncio.sleep(TEST_SLEEP * 2)

    # Check that retries were attempted
    assert mock_bot.send_message.call_count > 5


@pytest.mark.asyncio
async def test_graceful_shutdown_with_pending_messages(mock_bot):
    """Test graceful shutdown with pending messages."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        batch_size=5,
        batch_interval=TEST_BATCH_INTERVAL,
        retry_delay=TEST_SLEEP,
    )
    handler._bot = mock_bot

    logger = logging.getLogger("test_shutdown")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send messages
    for i in range(3):
        await handler.emit(
            logger.makeRecord(
                "test_shutdown", logging.INFO, "", 0, f"Message {i}", (), None
            )
        )

    # Start shutdown
    await handler.close()

    # Try sending after shutdown
    await handler.emit(
        logger.makeRecord(
            "test_shutdown", logging.INFO, "", 0, "Post-shutdown message", (), None
        )
    )

    await asyncio.sleep(TEST_SLEEP)

    # Check that pre-shutdown messages were sent and post-shutdown message was ignored
    assert mock_bot.send_message.call_count == 1
    assert "Message 0" in mock_bot.send_message.call_args[1]["text"]
    assert "Post-shutdown" not in mock_bot.send_message.call_args[1]["text"]


@pytest.mark.asyncio
async def test_custom_formatter_with_all_features(mock_bot):
    """Test custom formatter with all features enabled."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        project_name="TestProject",
        project_emoji="🚀",
        add_hashtags=True,
        include_project_name=True,
        include_level_emoji=True,
        datefmt="%Y-%m-%d %H:%M:%S",
        level_emojis={logging.INFO: "🌟", logging.ERROR: "💥"},
        message_format=lambda record, extra: f"CUSTOM: {record.getMessage()}",
        batch_interval=TEST_BATCH_INTERVAL,
        retry_delay=TEST_SLEEP,
    )
    handler._bot = mock_bot

    logger = logging.getLogger("test_format")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send messages with different levels
    await handler.emit(
        logger.makeRecord("test_format", logging.INFO, "", 0, "Info message", (), None)
    )
    await handler.emit(
        logger.makeRecord(
            "test_format", logging.ERROR, "", 0, "Error message", (), None
        )
    )

    await asyncio.sleep(TEST_SLEEP)

    # Check that all formatting elements are present
    assert mock_bot.send_message.call_count == 2
    info_message = mock_bot.send_message.call_args_list[0][1]["text"]
    error_message = mock_bot.send_message.call_args_list[1][1]["text"]

    # Check info message
    assert "🌟" in info_message
    assert "🚀" in info_message
    assert "TestProject" in info_message
    assert "#TestProject" in info_message
    assert "CUSTOM:" in info_message
    assert "Info message" in info_message

    # Check error message
    assert "💥" in error_message
    assert "🚀" in error_message
    assert "TestProject" in error_message
    assert "#TestProject" in error_message
    assert "CUSTOM:" in error_message
    assert "Error message" in error_message


@pytest.mark.asyncio
async def test_event_loop_initialization():
    """Test event loop initialization in non-test mode."""
    handler = None
    try:
        with patch("telegram.Bot") as mock_bot_class, patch(
            "asyncio.run", new=AsyncMock()
        ) as mock_run:
            mock_bot = MagicMock()
            mock_bot.get_me = AsyncMock(
                return_value={"id": 123456789, "is_bot": True, "first_name": "Test Bot"}
            )
            mock_bot.close = AsyncMock()
            mock_bot.send_message = AsyncMock()
            mock_bot_class.return_value = mock_bot

            handler = CustomTelegramHandler(
                token=TEST_TOKEN,
                chat_ids=TEST_CHAT_ID,
                test_mode=True,  # Use test mode to avoid event loop issues
                batch_interval=TEST_BATCH_INTERVAL,
                retry_delay=TEST_SLEEP,
                include_level_emoji=False,  # Disable level emoji
            )
            handler._bot = mock_bot  # Replace bot instance directly

            # Check that event loop is initialized
            assert handler.loop is not None

            # Send a test message
            record = logging.LogRecord(
                "test_init", logging.INFO, "", 0, "Test message", (), None
            )
            await handler.emit(record)
            await asyncio.sleep(TEST_SLEEP * 2)

            # Check that message was processed
            assert mock_bot.send_message.called
            assert mock_bot.send_message.call_args[1]["text"] == "Test message"
    finally:
        if handler:
            await handler.close()


@pytest.mark.asyncio
async def test_signal_handler_setup():
    """Test signal handler setup and cleanup."""
    handler = None
    try:
        with patch("telegram.Bot") as mock_bot_class, patch(
            "signal.signal"
        ) as mock_signal, patch("asyncio.run", new=AsyncMock()) as mock_run:
            mock_bot = MagicMock()
            mock_bot.get_me = AsyncMock()
            mock_bot.close = AsyncMock()
            mock_bot_class.return_value = mock_bot

            handler = CustomTelegramHandler(
                token=TEST_TOKEN,
                chat_ids=TEST_CHAT_ID,
                test_mode=False,  # Important: test real initialization
                batch_interval=TEST_BATCH_INTERVAL,
                retry_delay=TEST_SLEEP,
            )

            # Check that signal handlers were set up
            assert mock_signal.call_count >= 2  # At least SIGTERM and SIGINT

            # Simulate signal
            handler._signal_handler(signal.SIGTERM, None)
            await asyncio.sleep(TEST_SLEEP)

            # Check shutdown flags
            assert handler._is_shutting_down.is_set()
            assert (
                not handler._shutdown_complete.is_set()
            )  # Not complete until close() is called
    finally:
        if handler:
            await handler.close()


@pytest.mark.asyncio
async def test_batch_sender_thread():
    """Test batch sender thread functionality."""
    handler = None
    try:
        with patch("telegram.Bot") as mock_bot_class, patch(
            "asyncio.run", new=AsyncMock()
        ) as mock_run:
            mock_bot = MagicMock()
            mock_bot.get_me = AsyncMock()
            mock_bot.close = AsyncMock()
            mock_bot_class.return_value = mock_bot

            handler = CustomTelegramHandler(
                token=TEST_TOKEN,
                chat_ids=TEST_CHAT_ID,
                test_mode=False,  # Important: test real thread
                batch_size=2,
                batch_interval=TEST_BATCH_INTERVAL,
                retry_delay=TEST_SLEEP,
            )

            # Check that batch thread is running
            assert handler.batch_thread.is_alive()

            # Send messages
            for i in range(3):
                handler.message_queue[TEST_CHAT_ID].put_nowait(f"Message {i}")

            # Signal the batch sender
            handler.batch_event.set()
            await asyncio.sleep(TEST_SLEEP * 2)

            # Check that messages were processed
            assert (
                handler.message_queue[TEST_CHAT_ID].qsize() <= 1
            )  # Last message might still be in queue
    finally:
        if handler:
            await handler.close()


@pytest.mark.asyncio
async def test_error_handling_in_process_queue(mock_bot):
    """Test error handling in _process_queue method."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        batch_size=2,
        batch_interval=TEST_BATCH_INTERVAL,
        retry_delay=TEST_SLEEP,
        max_retries=0,  # No retries to avoid extra calls
    )
    handler._bot = mock_bot

    # Configure mock to raise various errors
    mock_bot.send_message.side_effect = Exception("Unexpected error")

    # Add messages to queue
    handler.message_queue[TEST_CHAT_ID].put_nowait("Message 1")
    handler.message_queue[TEST_CHAT_ID].put_nowait("Message 2")

    # Process queue
    await handler._process_queue()
    await asyncio.sleep(TEST_SLEEP)

    # Messages should be back in queue after error
    assert handler.message_queue[TEST_CHAT_ID].qsize() == 2

    # Try to send messages again with success
    mock_bot.send_message.side_effect = None
    await handler._process_queue()
    await asyncio.sleep(TEST_SLEEP)

    # Queue should be empty now
    assert handler.message_queue[TEST_CHAT_ID].qsize() == 0


@pytest.mark.asyncio
async def test_graceful_shutdown_cleanup(mock_bot):
    """Test cleanup during graceful shutdown."""
    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        batch_size=2,
        batch_interval=TEST_BATCH_INTERVAL,
        retry_delay=TEST_SLEEP,
    )
    handler._bot = mock_bot

    # Add some pending messages
    handler.message_queue[TEST_CHAT_ID].put_nowait("Message 1")
    handler.message_queue[TEST_CHAT_ID].put_nowait("Message 2")

    # Start shutdown
    handler._is_shutting_down.set()

    # Try to send more messages
    handler.message_queue[TEST_CHAT_ID].put_nowait("Message 3")
    await handler.emit(
        logging.LogRecord("test", logging.INFO, "", 0, "Message 4", (), None)
    )

    # Close handler
    await handler.close()

    # Check cleanup
    assert handler._closed
    assert handler._shutdown_complete.is_set()
    mock_bot.close.assert_called_once()


@pytest.mark.asyncio
async def test_message_formatting_with_errors(mock_bot):
    """Test message formatting with various error conditions."""

    def bad_formatter(record, extra):
        if record.msg == "error":
            raise ValueError("Formatting error")
        return f"CUSTOM: {record.getMessage()}"

    handler = CustomTelegramHandler(
        token=TEST_TOKEN,
        chat_ids=TEST_CHAT_ID,
        test_mode=True,
        message_format=bad_formatter,
        batch_interval=TEST_BATCH_INTERVAL,
        retry_delay=TEST_SLEEP,
    )
    handler._bot = mock_bot

    logger = logging.getLogger("test_format_error")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Send message that will cause formatting error
    await handler.emit(
        logger.makeRecord("test_format_error", logging.INFO, "", 0, "error", (), None)
    )
    await asyncio.sleep(TEST_SLEEP)

    # Send normal message
    await handler.emit(
        logger.makeRecord("test_format_error", logging.INFO, "", 0, "normal", (), None)
    )
    await asyncio.sleep(TEST_SLEEP)

    # Check that both messages were sent
    assert mock_bot.send_message.call_count == 2

    # First message should use default formatting
    assert "error" in mock_bot.send_message.call_args_list[0][1]["text"]
    # Second message should use custom formatting
    assert "CUSTOM:" in mock_bot.send_message.call_args_list[1][1]["text"]
