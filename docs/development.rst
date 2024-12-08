Development Guide
================

This guide will help you set up your development environment and contribute to TGBot-Logging.

Development Setup
---------------

1. Clone the repository:

   .. code-block:: bash

       git clone https://github.com/bykovk-pro/tgbot-logging.git
       cd tgbot-logging

2. Create and activate a virtual environment:

   .. code-block:: bash

       python -m venv venv
       source venv/bin/activate  # Linux/macOS
       # or
       .\venv\Scripts\activate  # Windows

3. Install development dependencies:

   .. code-block:: bash

       pip install -e ".[dev]"
       # or
       pip install -r requirements-dev.txt

Project Structure
---------------

.. code-block:: text

    tgbot-logging/
    ├── docs/               # Documentation
    ├── examples/           # Example scripts
    ├── src/               # Source code
    │   └── tgbot_logging/
    │       ├── __init__.py
    │       └── handler.py
    ├── tests/             # Test files
    ├── .env.example       # Environment variables example
    ├── setup.py           # Package configuration
    ├── requirements.txt   # Production dependencies
    └── requirements-dev.txt  # Development dependencies

Testing
-------

Run tests using pytest:

.. code-block:: bash

    pytest --cov=tgbot_logging --cov-report=term-missing

Current code coverage is 92%. The uncovered lines are mostly related to error handling and edge cases.

For manual testing, you can use the test bot script:

.. code-block:: bash

    python tests/test_bot.py

Code Style
---------

We use the following tools for code formatting and linting:

* black - Code formatter
* isort - Import sorter
* flake8 - Style guide enforcement

Format your code:

.. code-block:: bash

    black src tests examples
    isort src tests examples
    flake8 src tests examples

Documentation
------------

Build documentation locally:

.. code-block:: bash

    cd docs
    make html

View the documentation:

.. code-block:: bash

    open _build/html/index.html  # macOS
    # or
    xdg-open _build/html/index.html  # Linux
    # or
    start _build/html/index.html  # Windows

Building and Distribution
-----------------------

1. Update version in ``src/tgbot_logging/__init__.py`` and ``setup.py``

2. Build the package:

   .. code-block:: bash

       python -m build

3. Upload to PyPI:

   .. code-block:: bash

       python -m twine upload dist/*

Contributing
-----------

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

Pull Request Guidelines
---------------------

* Include tests for new features
* Update documentation as needed
* Follow the existing code style (black)
* Write clear commit messages
* Add yourself to CONTRIBUTORS.md

Security
--------

* Never commit sensitive data (tokens, passwords, etc.)
* Use environment variables for configuration
* Report security issues privately
* Keep dependencies up to date

Release Process
-------------

1. Update CHANGELOG.md
2. Update version number in both __init__.py and setup.py
3. Create release branch
4. Run full test suite with coverage
5. Build and test package
6. Create GitHub release
7. Upload to PyPI

Troubleshooting
--------------

Common Issues
~~~~~~~~~~~~

1. Rate Limiting
   
   * Telegram has rate limits for bots
   * Use batch_size and batch_interval
   * Handle RetryAfter exceptions

2. Message Formatting
   
   * HTML and MarkdownV2 have specific requirements
   * Escape special characters
   * Test formatting in Telegram first

3. Environment Variables
   
   * Check .env file location
   * Verify variable names
   * Use correct data types

Getting Help
~~~~~~~~~~~

* Open an issue on GitHub
* Check existing issues
* Read the FAQ
* Join our Telegram group 