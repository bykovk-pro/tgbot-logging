Welcome to TGBot-Logging's documentation!
=====================================

TGBot-Logging is a Python logging handler that sends log messages to Telegram chats with advanced features like message batching, retries, and formatting.

Features
--------

* Send log messages to one or multiple Telegram chats
* Support for HTML and MarkdownV2 formatting
* Message batching for better performance
* Automatic retries for failed messages
* Rate limiting and error handling
* Customizable log format and emojis
* Support for project names and hashtags
* Environment variables support
* Async/await support
* Cross-platform compatibility
* Type hints and documentation
* 96% test coverage

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   configuration
   examples
   api
   development
   changelog

Installation
-----------

Basic Installation (Production)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For basic usage in production environment:

.. code-block:: bash

    pip install tgbot-logging

Development Installation
~~~~~~~~~~~~~~~~~~~~~~

For development with testing tools and code formatting:

.. code-block:: bash

    pip install tgbot-logging[dev]
    # or
    pip install -r requirements-dev.txt

Documentation Tools
~~~~~~~~~~~~~~~~~

For building documentation:

.. code-block:: bash

    pip install tgbot-logging[docs]

Build Tools
~~~~~~~~~~

For package building and distribution:

.. code-block:: bash

    pip install tgbot-logging[build]

Full Installation
~~~~~~~~~~~~~~~

For all optional dependencies:

.. code-block:: bash

    pip install tgbot-logging[all]

Features in Detail
----------------

Message Formatting
~~~~~~~~~~~~~~~

* Support for HTML and MarkdownV2 formatting
* Custom message formats with templates
* Custom date/time formats
* Project names and emojis
* Automatic hashtags
* Level-specific emojis

Message Batching
~~~~~~~~~~~~~

* Configurable batch size
* Configurable batch interval
* Automatic batch flushing
* Memory-efficient queue system

Error Handling
~~~~~~~~~~~

* Automatic retries for failed messages
* Rate limit handling
* Network error handling
* Timeout handling
* Graceful error recovery

Performance
~~~~~~~~~

* Asynchronous message sending
* Message batching
* Rate limiting
* Memory optimization
* Cross-platform compatibility

Development Features
~~~~~~~~~~~~~~~~

* Type hints for better IDE support
* Comprehensive test suite (96% coverage)
* Detailed documentation
* Code style compliance (Black)
* Security checks (Bandit)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 