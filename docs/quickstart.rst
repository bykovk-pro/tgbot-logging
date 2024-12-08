Quick Start Guide
================

This guide will help you get started with TGBot-Logging quickly.

Setup
-----

1. Create a Telegram bot:
   
   * Open `@BotFather <https://t.me/botfather>`_ in Telegram
   * Send ``/newbot`` command
   * Follow instructions to create a bot
   * Copy the bot token (it looks like ``123456789:ABCdefGHIjklmNOPqrstUVwxyz``)

2. Get your chat ID:
   
   * Start a chat with your bot
   * Send any message to the bot
   * Open `@userinfobot <https://t.me/userinfobot>`_
   * Copy your chat ID (it's a number like ``123456789``)

3. Install the package:

   .. code-block:: bash

       pip install tgbot-logging

4. Configure environment variables:
   
   * Copy ``.env.example`` to ``.env``
   * Replace placeholder values with your actual credentials
   * Never commit ``.env`` file to version control

Basic Usage
----------

Here's a minimal example to get you started:

.. code-block:: python

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
    logger.error('This is an error message')

Async Usage
----------

The handler supports async/await syntax:

.. code-block:: python

    import asyncio
    import logging
    from tgbot_logging import TelegramHandler

    async def main():
        async with TelegramHandler(
            token='YOUR_BOT_TOKEN',
            chat_ids=['YOUR_CHAT_ID']
        ) as handler:
            logger = logging.getLogger('AsyncApp')
            logger.addHandler(handler)
            logger.info('Starting async operation...')
            await asyncio.sleep(1)
            logger.info('Operation completed')

    if __name__ == '__main__':
        asyncio.run(main())

Using Environment Variables
-------------------------

You can use environment variables for configuration:

.. code-block:: python

    import os
    from dotenv import load_dotenv
    from tgbot_logging import TelegramHandler

    # Load environment variables
    load_dotenv()

    # Create handler using environment variables
    handler = TelegramHandler(
        token=os.getenv('TELEGRAM_BOT_TOKEN'),
        chat_ids=[os.getenv('TELEGRAM_CHAT_ID')],
        level=os.getenv('LOG_LEVEL', 'INFO'),
        batch_size=int(os.getenv('BATCH_SIZE', 5)),
        batch_interval=float(os.getenv('BATCH_INTERVAL', 2.0))
    )

Message Formatting
----------------

HTML Formatting:

.. code-block:: python

    handler = TelegramHandler(
        token='YOUR_BOT_TOKEN',
        chat_ids=['YOUR_CHAT_ID'],
        parse_mode='HTML',
        fmt='<b>%(levelname)s</b> [%(asctime)s]\n%(message)s'
    )

    logger.info('Message with <b>bold text</b> and <i>italic text</i>')

MarkdownV2 Formatting:

.. code-block:: python

    handler = TelegramHandler(
        token='YOUR_BOT_TOKEN',
        chat_ids=['YOUR_CHAT_ID'],
        parse_mode='MarkdownV2',
        fmt='*%(levelname)s* \[%(asctime)s\]\n%(message)s'
    )

    logger.info('Message with *bold text* and _italic text_')

Message Batching
--------------

For better performance and to avoid rate limits:

.. code-block:: python

    handler = TelegramHandler(
        token='YOUR_BOT_TOKEN',
        chat_ids=['YOUR_CHAT_ID'],
        batch_size=5,  # Send messages in batches of 5
        batch_interval=1.0  # Wait up to 1 second to fill batch
    )

Next Steps
---------

* Check out the :doc:`examples` section for more advanced usage examples
* Read the :doc:`api` documentation for complete API reference
* See :doc:`development` guide for contributing to the project