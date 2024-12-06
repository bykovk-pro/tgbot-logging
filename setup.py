from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tgbot-logging",
    version="0.1.0",
    author="Kirill Bykov",
    author_email="me@bykovk.pro",
    description="A Python logging handler that sends log messages to Telegram chats",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bykovk-pro/tgbot-logging",
    project_urls={
        "Bug Tracker": "https://github.com/bykovk-pro/tgbot-logging/issues",
        "Documentation": "https://docs.bykovk.pro/",
        "Source Code": "https://github.com/bykovk-pro/tgbot-logging",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Logging",
        "Framework :: AsyncIO",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.7",
    install_requires=[
        "python-telegram-bot>=21.0.1",
        "httpx>=0.25.2",
    ],
    extras_require={
        # Development dependencies
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.23.2",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "isort>=5.13.0",
            "flake8>=6.1.0",
            "pylint>=3.0.2",
            "mypy>=1.7.1",
            "bandit>=1.7.5",
            "safety>=2.3.5",
        ],
        # Documentation dependencies
        "docs": [
            "sphinx>=7.1.2",
            "sphinx-rtd-theme>=2.0.0",
            "sphinx-autodoc-typehints>=1.25.2",
            "sphinx-intl>=2.1.0",
            "babel>=2.14.0",
        ],
        # Build and distribution dependencies
        "build": [
            "wheel>=0.42.0",
            "twine>=4.0.2",
            "build>=1.0.3",
        ],
        # All optional dependencies
        "all": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.23.2",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "isort>=5.13.0",
            "flake8>=6.1.0",
            "pylint>=3.0.2",
            "mypy>=1.7.1",
            "bandit>=1.7.5",
            "safety>=2.3.5",
            "sphinx>=7.1.2",
            "sphinx-rtd-theme>=2.0.0",
            "sphinx-autodoc-typehints>=1.25.2",
            "sphinx-intl>=2.1.0",
            "babel>=2.14.0",
            "wheel>=0.42.0",
            "twine>=4.0.2",
            "build>=1.0.3",
        ],
    },
) 