# TGBot-Logging

[![PyPI version](https://badge.fury.io/py/tgbot-logging.svg)](https://badge.fury.io/py/tgbot-logging)
[![Python Support](https://img.shields.io/pypi/pyversions/tgbot-logging.svg)](https://pypi.org/project/tgbot-logging/)
[![Documentation Status](https://readthedocs.org/projects/tgbot-logging/badge/?version=latest)](https://tgbot-logging.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python logging handler that sends log messages to Telegram chats.

## Features

- Send log messages to one or multiple Telegram chats
- Support for HTML and MarkdownV2 formatting
- Message batching for better performance
- Automatic retries for failed messages
- Customizable log format
- Environment variables support

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
    level=logging.INFO
)

# Add handler to logger
logger.addHandler(telegram_handler)

# Example usage
logger.info('This is an info message')
```

## Documentation

Full documentation is available at [tgbot-logging.readthedocs.io](https://tgbot-logging.readthedocs.io/), including:

- Detailed installation instructions
- Configuration options
- Advanced usage examples
- API reference
- Development guide

## Development Installation

For development with testing tools and code formatting:

```bash
pip install -e ".[dev]"
# or
pip install -r requirements-dev.txt
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- [Documentation](https://tgbot-logging.readthedocs.io/)
- [GitHub Issues](https://github.com/bykovk-pro/tgbot-logging/issues)
- [PyPI Project](https://pypi.org/project/tgbot-logging/)
