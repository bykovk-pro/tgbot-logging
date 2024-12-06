Welcome to TGBot-Logging's documentation!
=====================================

TGBot-Logging is a Python logging handler that sends log messages to Telegram chats.
It provides an easy way to integrate Telegram notifications into your application's logging system.

Features
--------

* Send log messages to one or multiple Telegram chats
* Support for HTML and MarkdownV2 formatting
* Message batching for better performance
* Automatic retries for failed messages
* Customizable log format
* Asynchronous message sending
* Graceful error handling
* Cross-platform compatibility
* Environment variables support

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

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 