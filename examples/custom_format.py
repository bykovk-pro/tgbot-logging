import logging
import time
from datetime import datetime
from tgbot_logging import TelegramHandler


def minimal_format(record: logging.LogRecord, context: dict) -> str:
    """Minimal format: message and level only."""
    return f"[{record.levelname}] {record.getMessage()}"


def detailed_format(record: logging.LogRecord, context: dict) -> str:
    """Detailed format with additional information."""
    # Use formatter from context
    timestamp = context["formatter"].formatTime(record)

    parts = [
        f"🏢 <b>[{context['project_name']}]</b>",
        f"{context['level_emojis'].get(record.levelno, '🔵')}",
        f"<b>{record.levelname}</b>",
        f"[{timestamp}]",
        f"\n📍 {record.pathname}:{record.lineno}",
        f"\n💬 {record.getMessage()}",
    ]
    if record.exc_info:
        parts.append(
            f"\n⚠️ <code>{context['formatter'].formatException(record.exc_info)}</code>"
        )
    return " ".join(parts)


def monitoring_format(record: logging.LogRecord, context: dict) -> str:
    """Monitoring format with metrics."""
    level_colors = {
        "DEBUG": "⚪️",
        "INFO": "🟢",
        "WARNING": "🟡",
        "ERROR": "🔴",
        "CRITICAL": "⛔️",
    }

    # Use formatter from context
    timestamp = context["formatter"].formatTime(record)

    return (
        f"{level_colors.get(record.levelname, '⚪️')} "
        f"<b>[{context['project_name']}]</b> "
        f"{record.getMessage()} "
        f"| {timestamp} "
        f"| {record.threadName}"
    )


def test_custom_formats():
    # Create loggers for different projects with different formats
    projects = {
        "API Service": {
            "logger": logging.getLogger("API"),
            "format": minimal_format,
            "emoji": "🌐",
            "datefmt": "%H:%M:%S",  # Time only
        },
        "Database": {
            "logger": logging.getLogger("DB"),
            "format": detailed_format,
            "emoji": "🗄️",
            "datefmt": "%Y-%m-%d %H:%M:%S.%f",  # Full date with milliseconds
        },
        "Monitoring": {
            "logger": logging.getLogger("Monitor"),
            "format": monitoring_format,
            "emoji": "📊",
            "datefmt": "%d.%m.%Y %H:%M:%S",  # European date format
        },
    }

    # Configure loggers
    for project_name, config in projects.items():
        logger = config["logger"]
        logger.setLevel(logging.INFO)

        # Create handler with custom format
        handler = TelegramHandler(
            token="YOUR_BOT_TOKEN",  # Replace with your bot token
            chat_ids=["YOUR_CHAT_ID"],  # Replace with your chat ID
            project_name=project_name,
            project_emoji=config["emoji"],
            message_format=config["format"],
            batch_size=2,
            batch_interval=1.0,
        )
        logger.addHandler(handler)

    try:
        # API Service - minimal format
        api_logger = projects["API Service"]["logger"]
        api_logger.info("Request processed successfully")
        api_logger.warning("High latency detected")

        time.sleep(2)

        # Database - detailed format
        db_logger = projects["Database"]["logger"]
        db_logger.info("Connection pool initialized")
        try:
            raise ValueError("Failed to connect to replica")
        except Exception as e:
            db_logger.error("Database error occurred", exc_info=True)

        time.sleep(2)

        # Monitoring - format with metrics
        mon_logger = projects["Monitoring"]["logger"]
        mon_logger.info("CPU Usage: 45%")
        mon_logger.warning("Memory usage above 80%")
        mon_logger.error("Disk space critical: 95%")

        # Wait for all messages to be sent
        time.sleep(5)

    finally:
        # Close all handlers
        for config in projects.values():
            for handler in config["logger"].handlers:
                handler.close()
        time.sleep(2)


if __name__ == "__main__":
    print("🚀 Testing different log formats...\n")
    test_custom_formats()
    print("\n✨ Testing completed!")
