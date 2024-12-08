import logging
import time
from datetime import datetime
from tgbot_logging import TelegramHandler


def create_format(time_format: str):
    """Creates a formatting function with the specified time format."""

    def format_func(record: logging.LogRecord, context: dict) -> str:
        # Create formatter for each time format
        formatter = logging.Formatter(datefmt=time_format)

        # Get current time for verification
        current_time = datetime.now()

        # Format time in different ways for debugging
        timestamp1 = formatter.formatTime(record)
        timestamp2 = current_time.strftime(time_format)
        timestamp3 = time.strftime(time_format)

        print(f"\nDebug time format '{time_format}':")
        print(f"  - Using formatter: {timestamp1}")
        print(f"  - Using datetime: {timestamp2}")
        print(f"  - Using time: {timestamp3}")

        # Use datetime for formatting (more reliable method)
        timestamp = current_time.strftime(time_format)

        # Format message
        return (
            f"{context['project_emoji']} <b>[{context['project_name']}]</b>\n"
            f"{context['level_emojis'].get(record.levelno, '🔵')} <b>{record.levelname}</b>\n"
            f"⏰ {timestamp}\n"
            f"💬 {record.getMessage()}"
        )

    return format_func


def test_time_formats():
    # Various time formats for testing
    formats = {
        "Simple": {
            "format": "%H:%M:%S",
            "emoji": "⌚️",
            "description": "Time only (hours:minutes:seconds)",
        },
        "Full": {
            "format": "%Y-%m-%d %H:%M:%S",
            "emoji": "📅",
            "description": "Full date and time",
        },
        "European": {
            "format": "%d.%m.%Y %H:%M:%S",
            "emoji": "🇪🇺",
            "description": "European format",
        },
        "US": {
            "format": "%m/%d/%Y %I:%M:%S %p",
            "emoji": "🇺🇸",
            "description": "US format with AM/PM",
        },
        "ISO": {
            "format": "%Y-%m-%dT%H:%M:%S",  # Simplified ISO format
            "emoji": "🌐",
            "description": "ISO format",
        },
        "Custom": {
            "format": "%d %B %Y %H:%M:%S",  # Using full month name
            "emoji": "📆",
            "description": "Date with month name",
        },
    }

    # Create loggers for each format
    loggers = {}
    for name, config in formats.items():
        logger = logging.getLogger(f"TimeFormat.{name}")
        logger.setLevel(logging.INFO)

        # Create handler with time format
        handler = TelegramHandler(
            token="YOUR_BOT_TOKEN",  # Replace with your bot token
            chat_ids=["YOUR_CHAT_ID"],  # Replace with your chat ID
            project_name=f"Time Format: {name}",
            project_emoji=config["emoji"],
            message_format=create_format(config["format"]),
            datefmt=config["format"],  # Add time format to handler
            batch_size=1,  # Send each message separately for clarity
            batch_interval=0.5,
        )
        logger.addHandler(handler)
        loggers[name] = logger

    try:
        # Send test messages
        print("🚀 Sending test messages with different time formats...")

        for name, config in formats.items():
            logger = loggers[name]
            print(f"\n📝 Testing format '{name}':")
            print(f"   Format: {config['format']}")
            print(f"   Description: {config['description']}")

            # Send message
            logger.info(f"Test message with time format: {config['format']}")
            time.sleep(1)  # Pause between messages

        # Send different logging levels for one format
        print("\n📊 Testing different logging levels with ISO format...")
        iso_logger = loggers["ISO"]
        iso_logger.debug("This is a debug message")
        iso_logger.info("This is an info message")
        iso_logger.warning("This is a warning message")
        iso_logger.error("This is an error message")
        iso_logger.critical("This is a critical message")

        # Wait for all messages to be sent
        print("\n⏳ Waiting for all messages to be sent...")
        time.sleep(5)

    finally:
        # Close all handlers
        for logger in loggers.values():
            for handler in logger.handlers:
                handler.close()
        time.sleep(2)


if __name__ == "__main__":
    print("🔍 Starting time format testing...\n")
    test_time_formats()
    print("\n✨ Testing completed!")
