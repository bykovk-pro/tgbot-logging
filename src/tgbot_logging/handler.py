"""
A handler class which sends logging records to a Telegram chat using a bot.

Args:
    token (str): Telegram Bot API token
    chat_ids (Union[str, int, List[Union[str, int]]]): Single chat ID or list of chat IDs
    level (int): Logging level (default: logging.NOTSET)
    fmt (str): Message format (default: None)
    parse_mode (str): Message parse mode ('HTML', 'MarkdownV2', None) (default: 'HTML')
    batch_size (int): Number of messages to batch before sending (default: 1)
    batch_interval (float): Maximum time to wait before sending a batch (seconds)
    max_retries (int): Maximum number of retries for failed messages (default: 3)
    retry_delay (float): Delay between retries (seconds) (default: 1.0)
    project_name (str): Project name to identify logs source (default: None)
    project_emoji (str): Emoji to use for project (default: '🔷')
    add_hashtags (bool): Whether to add project hashtag to messages (default: True)
    message_format (Callable): Custom message format function (default: None)
    level_emojis (Dict[int, str]): Custom emoji mapping for log levels (default: None)
    include_project_name (bool): Whether to include project name in message (default: True)
    include_level_emoji (bool): Whether to include level emoji (default: True)
    datefmt (str): Custom date format for timestamps (default: None)
    test_mode (bool): Whether to run in test mode (default: False)
"""

import logging
import asyncio
import time
import sys
import signal
import threading
from typing import Optional, Union, List, Dict, Callable, Any, NoReturn
from collections import defaultdict
from telegram import Bot
from telegram.error import TelegramError, RetryAfter, TimedOut, InvalidToken
from queue import Queue
from threading import Thread, Lock, Event
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

# Constants for shutdown
SHUTDOWN_TIMEOUT = 30  # seconds
FLUSH_TIMEOUT = 5  # seconds


class TelegramHandler(logging.Handler):
    """A handler class which sends logging records to a Telegram chat using a bot."""

    # Default emoji mapping for different log levels
    DEFAULT_LEVEL_EMOJI = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "🚨",
    }

    def __init__(
        self,
        token: str,
        chat_ids: Union[str, int, List[Union[str, int]]],
        level: int = logging.NOTSET,
        fmt: Optional[str] = None,
        parse_mode: Optional[str] = "HTML",
        batch_size: int = 1,
        batch_interval: float = 1.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        project_name: Optional[str] = None,
        project_emoji: str = "🔷",
        add_hashtags: bool = True,
        message_format: Optional[
            Callable[[logging.LogRecord, Dict[str, Any]], str]
        ] = None,
        level_emojis: Optional[Dict[int, str]] = None,
        include_project_name: bool = True,
        include_level_emoji: bool = True,
        datefmt: Optional[str] = None,
        test_mode: bool = False,
    ):
        """Initialize the handler."""
        super().__init__(level)
        self.token = token
        self.chat_ids = (
            [str(chat_ids)]
            if isinstance(chat_ids, (str, int))
            else [str(cid) for cid in chat_ids]
        )
        self.parse_mode = parse_mode
        self.batch_size = max(1, batch_size)
        self.batch_interval = max(0.1, batch_interval)
        self.max_retries = max(0, max_retries)
        self.retry_delay = max(0.1, retry_delay)
        self.project_name = project_name
        self.project_emoji = project_emoji
        self.add_hashtags = add_hashtags
        self.message_format = message_format
        self.level_emojis = level_emojis or self.DEFAULT_LEVEL_EMOJI.copy()
        self.include_project_name = include_project_name
        self.include_level_emoji = include_level_emoji
        self.datefmt = datefmt
        self.test_mode = test_mode

        # Initialize bot
        try:
            self._bot = Bot(token=token)
            # Try to validate token by getting bot info
            if not test_mode:
                asyncio.run(self._bot.get_me())
        except InvalidToken as e:
            raise InvalidToken(f"Invalid token: {str(e)}")
        except Exception as e:
            raise InvalidToken(f"Failed to initialize bot: {str(e)}")

        # Shutdown flags
        self._is_shutting_down = Event()
        self._shutdown_complete = Event()
        self._closed = False

        # Set formatter with custom date format
        if fmt is not None:
            self.formatter = logging.Formatter(fmt, datefmt=self.datefmt)
        else:
            self.formatter = logging.Formatter("%(message)s", datefmt=self.datefmt)

        # Create time formatter
        self.time_formatter = (
            logging.Formatter(datefmt=self.datefmt) if self.datefmt else None
        )

        # Initialize batching
        self.message_queue = defaultdict(Queue)
        self.batch_lock = Lock()
        self.batch_event = Event()
        self._last_batch_time = time.time()
        self._force_batch = False

        # Rate limiting state
        self.last_message_time = 0
        self.min_message_interval = 1

        # Create event loop in a separate thread if not in test mode
        if not test_mode:
            self.executor = ThreadPoolExecutor(max_workers=1)
            self.loop = asyncio.new_event_loop()
            if self.executor:
                self.executor.submit(self._run_event_loop)

            # Start batch sender thread
            self.batch_thread = Thread(target=self._batch_sender, daemon=True)
            if self.batch_thread:
                self.batch_thread.start()

            # Setup signal handlers
            self._setup_signal_handlers()
        else:
            # In test mode, use the current event loop
            self.loop = asyncio.get_event_loop()
            self.executor = None
            self.batch_thread = None

    async def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record.

        Format the record and send it to the specified chat.
        """
        if self._closed:
            return

        try:
            msg = self.format(record)
            for chat_id in self.chat_ids:
                try:
                    self.message_queue[chat_id].put_nowait(msg)
                except Exception as e:
                    print(f"Error adding message to queue for {chat_id}: {str(e)}")

            # In test mode, process messages based on batch size or force flag
            if self.test_mode:
                if self.batch_size == 1:
                    # For single messages, send immediately
                    await self._process_queue()
                else:
                    # For batched messages, check if we need to send
                    should_process = self._force_batch
                    if not should_process:
                        for chat_id in self.chat_ids:
                            if self.message_queue[chat_id].qsize() >= self.batch_size:
                                should_process = True
                                break
                    if should_process:
                        await self._process_queue()
            else:
                # Signal the batch sender thread
                self.batch_event.set()

        except Exception as e:
            print(f"Error in emit: {str(e)}")

    async def _process_queue(self) -> None:
        """Process messages in the queue."""
        try:
            for chat_id in self.chat_ids:
                messages = []
                try:
                    # Get all available messages from the queue
                    while (
                        not self.message_queue[chat_id].empty()
                        and len(messages) < self.batch_size
                    ):
                        messages.append(self.message_queue[chat_id].get_nowait())
                        self.message_queue[chat_id].task_done()

                    if messages:
                        # Join messages with double newline
                        text = "\n\n".join(messages)
                        try:
                            await self._send_message(chat_id, text)
                        except Exception as e:
                            print(f"Error sending message to {chat_id}: {str(e)}")
                            # Put messages back in queue for retry
                            for msg in messages:
                                self.message_queue[chat_id].put_nowait(msg)
                            # Try next chat ID
                            continue

                except Exception as e:
                    print(f"Error processing queue for {chat_id}: {str(e)}")

        except Exception as e:
            print(f"Error in _process_queue: {str(e)}")

    async def _send_message(self, chat_id: str, text: str) -> None:
        """Send a message to a chat."""
        retries = 0
        last_error = None
        while retries <= self.max_retries:
            try:
                await self._bot.send_message(
                    chat_id=chat_id, text=text, parse_mode=self.parse_mode
                )
                return  # Success
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after)
                retries += 1
                last_error = e
            except Exception as e:
                await asyncio.sleep(self.retry_delay)
                retries += 1
                last_error = e

        # If we get here, all retries failed
        if last_error:
            raise last_error

    def _batch_sender(self) -> None:
        """Background thread for sending batched messages."""
        while not self._is_shutting_down.is_set():
            # Wait for new messages or batch interval
            self.batch_event.wait(timeout=self.batch_interval)
            self.batch_event.clear()

            if not self._is_shutting_down.is_set():
                # Process queues
                asyncio.run_coroutine_threadsafe(
                    self._process_queue(), self.loop
                ).result()

    def _run_event_loop(self) -> None:
        """Run the event loop in a separate thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        # Always setup signal handlers in test mode
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            try:
                signal.signal(sig, self._signal_handler)
            except ValueError:
                # Can't set signal handler in thread
                pass

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        print(f"Received signal {signum}, initiating graceful shutdown...")
        # Schedule shutdown in the event loop
        if self.test_mode:
            asyncio.create_task(self.close())
        else:
            self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self.close()))

    async def close(self) -> None:
        """
        Close the handler.

        This method is called during shutdown. It ensures all messages are sent before closing.
        """
        if self._closed:
            return

        self._is_shutting_down.set()

        try:
            # Force process remaining messages
            self._force_batch = True
            await self._process_queue()
        except Exception as e:
            print(f"Error flushing queues: {str(e)}")

        try:
            # Close bot
            if hasattr(self._bot, "close"):
                await self._bot.close()
        except Exception as e:
            print(f"Error closing bot: {str(e)}")

        # Stop event loop and executor
        if not self.test_mode and self.loop and self.executor:
            self.loop.call_soon_threadsafe(self.loop.stop)
            # Schedule executor shutdown in a separate thread to avoid deadlock
            Thread(
                target=self.executor.shutdown, kwargs={"wait": True}, daemon=True
            ).start()

        self._closed = True
        self._shutdown_complete.set()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
