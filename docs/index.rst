Welcome to TGBot-Logging's documentation!
=========================================

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

   quickstart
   api
   examples
   development

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

    pip install -e ".[dev]"

Documentation Tools
~~~~~~~~~~~~~~~~~

For building documentation:

.. code-block:: bash

    pip install -e ".[docs]"

Build Tools
~~~~~~~~~~

For package building and distribution:

.. code-block:: bash

    pip install -e ".[build]"

Full Installation
~~~~~~~~~~~~~~~

For all optional dependencies:

.. code-block:: bash

    pip install -e ".[all]"

Features in Detail
----------------

Message Formatting
~~~~~~~~~~~~~~~~

* HTML and MarkdownV2 support
* Custom message formatting
* Emoji support
* Project name and hashtags

Message Batching
~~~~~~~~~~~~~~

* Configurable batch size
* Batch interval control
* Automatic retry on failure
* Rate limit handling

Error Handling
~~~~~~~~~~~~

* Network timeouts
* Rate limiting
* Invalid tokens/chat IDs
* Message sending failures
* Graceful shutdown

Performance
~~~~~~~~~~

* Async/await support
* Message batching
* Minimal memory footprint
* Resource cleanup

Development Features
~~~~~~~~~~~~~~~~~

* Type hints
* Comprehensive tests
* Code coverage (92%)
* Black code style
* Documentation

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 