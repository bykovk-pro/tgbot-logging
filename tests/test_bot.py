"""
Tests for Bot functionality.
"""

import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from telegram import Bot
from telegram.error import RetryAfter, NetworkError, TelegramError
from dotenv import load_dotenv

# Load test environment variables
load_dotenv("tests/.env.test")

# Test data
TEST_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "test_token")
TEST_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "123456789")
TEST_MESSAGE = "Test message"


@pytest.fixture
async def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock(spec=Bot)
    # Configure get_me to return a successful response
    me = MagicMock()
    me.first_name = "TestBot"
    me.username = "test_bot"
    bot.get_me = AsyncMock(return_value=me)
    # Configure send_message to return a successful response
    message = MagicMock()
    message.message_id = 12345
    bot.send_message = AsyncMock(return_value=message)
    bot.close = AsyncMock()
    return bot


@pytest.mark.asyncio
async def test_bot_initialization():
    """Test bot initialization."""
    bot = Bot(TEST_TOKEN)
    assert bot.token == TEST_TOKEN
    assert isinstance(bot, Bot)
    # No need to close the bot here as it's just testing initialization


@pytest.mark.asyncio
async def test_bot_get_me(mock_bot):
    """Test getting bot information."""
    me = await mock_bot.get_me()
    assert me.first_name == "TestBot"
    assert me.username == "test_bot"


@pytest.mark.asyncio
async def test_bot_send_message(mock_bot):
    """Test sending a message."""
    message = await mock_bot.send_message(chat_id=TEST_CHAT_ID, text=TEST_MESSAGE)
    assert message.message_id == 12345
    mock_bot.send_message.assert_called_once_with(
        chat_id=TEST_CHAT_ID, text=TEST_MESSAGE
    )


@pytest.mark.asyncio
async def test_bot_rate_limit(mock_bot):
    """Test handling rate limit errors."""
    # Configure send_message to raise RetryAfter first, then succeed
    message = MagicMock()
    message.message_id = 12345
    mock_bot.send_message.side_effect = [
        RetryAfter(0.1),  # First call raises RetryAfter
        message,  # Second call succeeds
    ]

    # First attempt should raise RetryAfter
    with pytest.raises(RetryAfter):
        await mock_bot.send_message(chat_id=TEST_CHAT_ID, text=TEST_MESSAGE)

    # After waiting, second attempt should succeed
    await asyncio.sleep(0.1)
    message = await mock_bot.send_message(chat_id=TEST_CHAT_ID, text=TEST_MESSAGE)
    assert message.message_id == 12345


@pytest.mark.asyncio
async def test_bot_network_error(mock_bot):
    """Test handling network errors."""
    # Configure send_message to raise NetworkError
    mock_bot.send_message.side_effect = NetworkError("Test network error")

    with pytest.raises(NetworkError):
        await mock_bot.send_message(chat_id=TEST_CHAT_ID, text=TEST_MESSAGE)


@pytest.mark.asyncio
async def test_bot_close(mock_bot):
    """Test bot cleanup."""
    await mock_bot.close()
    mock_bot.close.assert_called_once()
