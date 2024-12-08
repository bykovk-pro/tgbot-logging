"""
Examples and integration tests for TelegramHandler.

This script demonstrates real-world usage scenarios and serves as integration tests.
It requires a valid Telegram bot token and chat ID to be set in the .env file.

Features demonstrated:
- Basic logging functionality
- Message formatting and HTML support
- Message batching
- Multi-project logging
- Performance testing
- Error recovery testing
- Special characters handling

Usage:
    1. Create a .env file with TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
    2. Run this script: python tests/examples.py
"""

import logging
import time
import sys
import os
from dotenv import load_dotenv
from tgbot_logging import TelegramHandler

# Load environment variables
load_dotenv()

# Get configuration from environment
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env file")
    sys.exit(1)


def test_all_features():
    """Test all features of TelegramHandler."""
    # Create logger
    logger = logging.getLogger("TestLogger")
    logger.setLevel(logging.DEBUG)

    # Add console output for comparison
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create Telegram handler with project details
    telegram_handler = TelegramHandler(
        token=BOT_TOKEN,
        chat_ids=[CHAT_ID],
        level=logging.INFO,
        parse_mode="HTML",
        batch_size=5,  # Group by 5 messages
        batch_interval=3.0,  # Send every 3 seconds
        max_retries=3,
        retry_delay=2.0,
        project_name="MyTestProject",  # Project name
        project_emoji="🚀",  # Project emoji
        add_hashtags=True,  # Add hashtags
    )
    logger.addHandler(telegram_handler)

    try:
        # 1. Test different logging levels
        logger.debug("This is a debug message (should not be sent to Telegram)")
        logger.info("This is an info message")
        time.sleep(1)

        logger.warning("This is a warning message")
        time.sleep(1)

        logger.error("This is an error message")
        time.sleep(1)

        # 2. Test HTML formatting
        logger.info(
            "Message with <b>bold text</b>, <i>italic</i> and <code>monospace font</code>"
        )
        time.sleep(2)

        # 3. Test batching
        logger.info("Starting batch test...")
        for i in range(5):
            logger.info(f"Batch test message {i + 1}")
            time.sleep(0.5)

        time.sleep(3)

        # 4. Test error handling
        logger.info("Testing exception handling...")
        try:
            raise ValueError("This is a test error!")
        except Exception as e:
            logger.exception("An error occurred:")

        time.sleep(2)

        # 5. Test long messages
        logger.info(
            "Testing long message:\n"
            + "-" * 50
            + "\n"
            + "This is a very long message that should be properly formatted.\n"
            + "Testing line breaks and general formatting.\n"
            + "-" * 50
        )

        # Wait for all messages to be sent
        logger.info("Tests completed! Waiting for all messages to be sent...")
        time.sleep(5)

    finally:
        # Properly close handlers
        telegram_handler.close()
        console_handler.close()
        time.sleep(2)


def test_multiple_projects():
    """Demonstration of using different projects."""
    # Create loggers for different projects
    projects = {
        "Frontend": ("💻", logging.getLogger("Frontend")),
        "Backend": ("⚙️", logging.getLogger("Backend")),
        "Database": ("🗄️", logging.getLogger("Database")),
    }

    # Configure loggers
    for project_name, (emoji, logger) in projects.items():
        logger.setLevel(logging.INFO)

        # Create handler for each project
        handler = TelegramHandler(
            token=BOT_TOKEN,
            chat_ids=[CHAT_ID],
            level=logging.INFO,
            project_name=project_name,
            project_emoji=emoji,
            batch_size=2,
            batch_interval=1.0,
        )
        logger.addHandler(handler)

    try:
        # Simulate logs from different projects
        projects["Frontend"][1].info("User logged in")
        projects["Backend"][1].warning("High API load")
        projects["Database"][1].error("Replica connection error")

        time.sleep(2)

        projects["Frontend"][1].info("New order created")
        projects["Backend"][1].info("Order processed")
        projects["Database"][1].info("Transaction completed")

        # Wait for all messages to be sent
        time.sleep(5)

    finally:
        # Close all handlers
        for _, (_, logger) in projects.items():
            for handler in logger.handlers:
                handler.close()
        time.sleep(2)


def test_performance():
    """Test performance with high message volume."""
    logger = logging.getLogger("PerformanceTest")
    logger.setLevel(logging.INFO)

    # Create handler with small batch size and interval
    handler = TelegramHandler(
        token=BOT_TOKEN,
        chat_ids=[CHAT_ID],
        level=logging.INFO,
        project_name="PerformanceTest",
        project_emoji="⚡",
        batch_size=10,
        batch_interval=1.0,
    )
    logger.addHandler(handler)

    try:
        # Send many messages quickly
        logger.info("Starting performance test...")
        for i in range(50):
            logger.info(f"Performance test message {i + 1}")
            time.sleep(0.1)  # Small delay to avoid overwhelming

        logger.info("Performance test completed!")
        time.sleep(5)  # Wait for all messages to be sent

    finally:
        handler.close()
        time.sleep(2)


def test_error_recovery():
    """Test error recovery mechanisms."""
    logger = logging.getLogger("ErrorTest")
    logger.setLevel(logging.INFO)

    # Create handler with aggressive retry settings
    handler = TelegramHandler(
        token=BOT_TOKEN,
        chat_ids=[CHAT_ID],
        level=logging.INFO,
        project_name="ErrorTest",
        project_emoji="🔧",
        max_retries=5,
        retry_delay=1.0,
    )
    logger.addHandler(handler)

    try:
        # Test various error scenarios
        logger.info("Starting error recovery test...")

        # Test long message handling
        logger.info("A" * 5000)  # Message longer than Telegram's limit

        # Test special characters
        logger.info("Special chars: 🎉 👍 \u200b \x00 \uFFFD")

        # Test HTML escaping
        logger.info('<script>alert("test")</script>')

        logger.info("Error recovery test completed!")
        time.sleep(5)

    finally:
        handler.close()
        time.sleep(2)


if __name__ == "__main__":
    print("🚀 Starting manual tests...\n")

    print("1. Testing basic functionality...")
    test_all_features()

    print("\n2. Testing work with different projects...")
    test_multiple_projects()

    print("\n3. Testing performance...")
    test_performance()

    print("\n4. Testing error recovery...")
    test_error_recovery()

    print("\n✨ Testing completed!")
