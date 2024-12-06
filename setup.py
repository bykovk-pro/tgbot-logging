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
        "Documentation": "https://github.com/bykovk-pro/tgbot-logging/docs",
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
        "python-telegram-bot>=20.0",
    ],
    extras_require={
        # Development dependencies
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.14.0",
            "black>=21.0",
            "isort>=5.0",
            "flake8>=3.9",
        ],
        # Documentation dependencies
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autodoc-typehints>=1.12.0",
            "babel>=2.9.1",
        ],
        # Build and distribution dependencies
        "build": [
            "wheel>=0.37.0",
            "twine>=3.4.0",
        ],
        # All optional dependencies
        "all": [
            "pytest>=6.0",
            "pytest-asyncio>=0.14.0",
            "black>=21.0",
            "isort>=5.0",
            "flake8>=3.9",
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autodoc-typehints>=1.12.0",
            "babel>=2.9.1",
            "wheel>=0.37.0",
            "twine>=3.4.0",
        ],
    },
) 