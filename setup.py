"""Setup script for tgbot-logging."""

from setuptools import setup, find_packages

# Read README.md for long description
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="tgbot-logging",
    version="1.0.2",  # Updated version with new features
    author="Kirill Bykov",
    author_email="me@bykovk.pro",
    description="A Python logging handler that sends log messages to Telegram chats",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bykovk-pro/tgbot-logging",
    project_urls={
        "Documentation": "https://tgbot-logging.readthedocs.io/",
        "Bug Reports": "https://github.com/bykovk-pro/tgbot-logging/issues",
        "Source Code": "https://github.com/bykovk-pro/tgbot-logging",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Logging",
        "Topic :: Communications :: Chat",
        "Framework :: AsyncIO",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=[
        "python-telegram-bot>=20.0",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "mypy>=0.990",
            "bandit>=1.7.0",
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    keywords=[
        "telegram",
        "logging",
        "handler",
        "async",
        "batching",
        "monitoring",
        "notifications",
        "chat",
        "bot",
        "signal",
        "shutdown",
        "graceful",
    ],
)
