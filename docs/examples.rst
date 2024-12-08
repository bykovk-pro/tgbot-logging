Examples
========

This section provides various examples of using TGBot-Logging in different scenarios.

Basic Usage
----------

Simple logging setup:

.. literalinclude:: ../examples/basic_usage.py
   :language: python
   :linenos:
   :caption: examples/basic_usage.py

Custom Message Formats
--------------------

Different message formatting options:

.. literalinclude:: ../examples/custom_format.py
   :language: python
   :linenos:
   :caption: examples/custom_format.py

Time Formats
-----------

Various time formatting examples:

.. literalinclude:: ../examples/time_formats.py
   :language: python
   :linenos:
   :caption: examples/time_formats.py

Multiple Projects
---------------

Example of using the handler with multiple projects:

.. code-block:: python

    from tgbot_logging import TelegramHandler
    import logging

    # Create loggers for different projects
    projects = {
        'Frontend': ('💻', logging.getLogger('Frontend')),
        'Backend': ('⚙️', logging.getLogger('Backend')),
        'Database': ('🗄️', logging.getLogger('Database'))
    }
    
    # Configure loggers
    for project_name, (emoji, logger) in projects.items():
        logger.setLevel(logging.INFO)
        
        handler = TelegramHandler(
            token='YOUR_BOT_TOKEN',
            chat_ids=['YOUR_CHAT_ID'],
            level=logging.INFO,
            project_name=project_name,
            project_emoji=emoji,
            batch_size=2,
            batch_interval=1.0
        )
        logger.addHandler(handler)
    
    # Usage example
    projects['Frontend'][1].info('User logged in')
    projects['Backend'][1].warning('High API load')
    projects['Database'][1].error('Replica connection error')

Error Handling
-------------

Example with error handling and retries:

.. code-block:: python

    import logging
    from tgbot_logging import TelegramHandler

    logger = logging.getLogger('ErrorTest')
    handler = TelegramHandler(
        token='YOUR_BOT_TOKEN',
        chat_ids=['YOUR_CHAT_ID'],
        max_retries=3,
        retry_delay=1.0
    )
    logger.addHandler(handler)

    try:
        # Some code that might fail
        result = 1 / 0
    except Exception as e:
        # This will include the full traceback
        logger.exception('An error occurred:')

Environment Variables
-------------------

Using environment variables for configuration:

.. code-block:: python

    import os
    from dotenv import load_dotenv
    from tgbot_logging import TelegramHandler

    # Load environment variables
    load_dotenv()

    handler = TelegramHandler(
        token=os.getenv('TELEGRAM_BOT_TOKEN'),
        chat_ids=[os.getenv('TELEGRAM_CHAT_ID')],
        level=os.getenv('LOG_LEVEL', 'INFO'),
        batch_size=int(os.getenv('BATCH_SIZE', 5)),
        batch_interval=float(os.getenv('BATCH_INTERVAL', 2.0)),
        project_name=os.getenv('PROJECT_NAME', 'MyProject'),
        project_emoji=os.getenv('PROJECT_EMOJI', '🚀')
    )

Custom Emoji Mapping
------------------

Customizing emojis for different log levels:

.. code-block:: python

    custom_emojis = {
        logging.DEBUG: '🐛',
        logging.INFO: '📝',
        logging.WARNING: '⚡️',
        logging.ERROR: '💥',
        logging.CRITICAL: '🆘'
    }

    handler = TelegramHandler(
        token='YOUR_BOT_TOKEN',
        chat_ids=['YOUR_CHAT_ID'],
        level_emojis=custom_emojis
    )

Async Usage
----------

Using the handler in an async application:

.. code-block:: python

    import asyncio
    import logging
    from tgbot_logging import TelegramHandler

    async def main():
        logger = logging.getLogger('AsyncApp')
        handler = TelegramHandler(
            token='YOUR_BOT_TOKEN',
            chat_ids=['YOUR_CHAT_ID']
        )
        logger.addHandler(handler)

        try:
            # Your async code here
            logger.info('Starting async operation...')
            await asyncio.sleep(1)
            logger.info('Async operation completed')

        finally:
            # Properly close the handler
            handler.close()
            await asyncio.sleep(1)  # Wait for pending messages

    if __name__ == '__main__':
        asyncio.run(main()) 