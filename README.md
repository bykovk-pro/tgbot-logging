# TGBot-Logging

[![PyPI version](https://badge.fury.io/py/tgbot-logging.svg)](https://badge.fury.io/py/tgbot-logging)
[![Python Support](https://img.shields.io/pypi/pyversions/tgbot-logging.svg)](https://pypi.org/project/tgbot-logging/)
[![Documentation Status](https://readthedocs.org/projects/tgbot-logging/badge/?version=latest)](https://tgbot-logging.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen.svg)](https://github.com/bykovk-pro/tgbot-logging)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python logging handler that sends log messages to Telegram chats with advanced features like message batching, retries, and formatting.

## Features

- Send log messages to one or multiple Telegram chats
- Support for HTML and MarkdownV2 formatting
- Message batching for better performance
- Automatic retries for failed messages
- Rate limiting and error handling
- Customizable log format and emojis
- Support for project names and hashtags
- Environment variables support
- Async/await support
- Cross-platform compatibility
- Type hints and documentation
- 96% test coverage

## Quick Start

1. Install the package:
```bash
pip install tgbot-logging
```

2. Basic usage:
```python
import logging
from tgbot_logging import TelegramHandler

# Create logger
logger = logging.getLogger('MyApp')
logger.setLevel(logging.DEBUG)

# Create TelegramHandler
telegram_handler = TelegramHandler(
    token='YOUR_BOT_TOKEN',
    chat_ids=['YOUR_CHAT_ID'],
    level=logging.INFO,
    project_name='MyApp',  # Optional project name
    project_emoji='🚀',    # Optional project emoji
    parse_mode='HTML'      # Support for HTML formatting
)

# Add handler to logger
logger.addHandler(telegram_handler)

# Example usage
logger.info('This is an info message')
logger.error('This is an error message')
```

3. Advanced usage with batching and retries:
```python
telegram_handler = TelegramHandler(
    token='YOUR_BOT_TOKEN',
    chat_ids=['YOUR_CHAT_ID'],
    level=logging.INFO,
    batch_size=5,           # Batch 5 messages together
    batch_interval=2.0,     # Send batch every 2 seconds or when full
    max_retries=3,          # Retry failed messages 3 times
    retry_delay=1.0,        # Wait 1 second between retries
    parse_mode='HTML',      # Support for HTML formatting
    fmt='<b>%(levelname)s</b> [%(asctime)s]\n%(message)s'  # Custom HTML format
)
```

4. Environment variables support:
```bash
# .env file
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_IDS=123456789,987654321
LOG_LEVEL=INFO
BATCH_SIZE=5
BATCH_INTERVAL=2.0
MAX_RETRIES=3
RETRY_DELAY=1.0
PARSE_MODE=HTML
PROJECT_NAME=MyProject
PROJECT_EMOJI=🚀
```

## Documentation

Full documentation is available at [tgbot-logging.readthedocs.io](https://tgbot-logging.readthedocs.io/), including:

- Detailed installation instructions
- Configuration options
- Advanced usage examples
- API reference
- Development guide

## Features in Detail

### Message Formatting

- Support for HTML and MarkdownV2 formatting
- Custom message formats with templates
- Custom date/time formats
- Project names and emojis
- Automatic hashtags
- Level-specific emojis

### Message Batching

- Configurable batch size
- Configurable batch interval
- Automatic batch flushing
- Memory-efficient queue system

### Error Handling

- Automatic retries for failed messages
- Rate limit handling
- Network error handling
- Timeout handling
- Graceful error recovery

### Performance

- Asynchronous message sending
- Message batching
- Rate limiting
- Memory optimization
- Cross-platform compatibility

### Development Features

- Type hints for better IDE support
- Comprehensive test suite (96% coverage)
- Detailed documentation
- Code style compliance (Black)
- Security checks (Bandit)

## Development Installation

For development with testing tools and code formatting:

```bash
pip install -e ".[dev]"
# or
pip install -r requirements-dev.txt
```

## Testing

Run tests with coverage report:

```bash
pytest -v --cov=tgbot_logging --cov-report=term-missing:skip-covered
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- [Documentation](https://tgbot-logging.readthedocs.io/)
- [GitHub Issues](https://github.com/bykovk-pro/tgbot-logging/issues)
- [PyPI Project](https://pypi.org/project/tgbot-logging/)
