API Reference
=============

This section provides detailed API documentation for the TGBot-Logging package.

TelegramHandler
--------------

.. autoclass:: tgbot_logging.TelegramHandler
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Configuration Options
--------------------

The ``TelegramHandler`` class accepts the following parameters:

Required Parameters
~~~~~~~~~~~~~~~~~~

``token`` (str)
    Telegram Bot API token obtained from @BotFather

``chat_ids`` (Union[str, int, List[Union[str, int]]])
    Single chat ID or list of chat IDs where messages will be sent

Optional Parameters
~~~~~~~~~~~~~~~~~~

``level`` (int)
    Minimum logging level (default: logging.NOTSET)

``fmt`` (str)
    Message format string (default: None)

``parse_mode`` (str)
    Message parse mode ('HTML', 'MarkdownV2', None) (default: 'HTML')

``batch_size`` (int)
    Number of messages to batch before sending (default: 1)

``batch_interval`` (float)
    Maximum time to wait before sending a batch (seconds) (default: 1.0)

``max_retries`` (int)
    Maximum number of retries for failed messages (default: 3)

``retry_delay`` (float)
    Delay between retries (seconds) (default: 1.0)

``project_name`` (str)
    Project name to identify logs source (default: None)

``project_emoji`` (str)
    Emoji to use for project (default: '🔷')

``add_hashtags`` (bool)
    Whether to add project hashtag to messages (default: True)

``message_format`` (Callable)
    Custom message format function (default: None)

``level_emojis`` (Dict[int, str])
    Custom emoji mapping for log levels (default: None)

``include_project_name`` (bool)
    Whether to include project name in message (default: True)

``include_level_emoji`` (bool)
    Whether to include level emoji (default: True)

``datefmt`` (str)
    Custom date format for timestamps (default: None)

``test_mode`` (bool)
    Whether to run in test mode (default: False)

Default Level Emojis
-------------------

The handler comes with default emojis for different log levels:

.. code-block:: python

    DEFAULT_LEVEL_EMOJI = {
        logging.DEBUG: '🔍',
        logging.INFO: 'ℹ️',
        logging.WARNING: '⚠️',
        logging.ERROR: '❌',
        logging.CRITICAL: '🚨',
    }

Custom Message Formatting
-----------------------

You can provide a custom message formatting function:

.. code-block:: python

    def custom_format(record: logging.LogRecord, context: dict) -> str:
        """Custom message formatting function.
        
        Args:
            record: The logging record
            context: Dictionary with formatting context
        
        Returns:
            str: Formatted message
        """
        return f"{context['project_emoji']} {record.getMessage()}"

    handler = TelegramHandler(
        token='YOUR_BOT_TOKEN',
        chat_ids=['YOUR_CHAT_ID'],
        message_format=custom_format
    )

The context dictionary provides:

* project_name
* project_emoji
* level_emojis
* parse_mode
* formatter
* time_formatter
* format_time function

Error Handling
-------------

The handler includes built-in error handling for:

* Rate limiting (RetryAfter)
* Network timeouts
* Message sending failures
* Invalid tokens or chat IDs
* Graceful shutdown

All errors are handled gracefully with automatic retries where appropriate.

Async Support
------------

The handler supports async/await syntax and can be used as an async context manager:

.. code-block:: python

    async with TelegramHandler(token='YOUR_BOT_TOKEN', chat_ids=['YOUR_CHAT_ID']) as handler:
        logger = logging.getLogger('AsyncApp')
        logger.addHandler(handler)
        logger.info('This message will be sent asynchronously')

The handler will automatically close and clean up resources when exiting the context. 