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

# Constants for shutdown
SHUTDOWN_TIMEOUT = 30  # seconds
FLUSH_TIMEOUT = 5  # seconds

class TelegramHandler(logging.Handler):
    """A handler class which sends logging records to a Telegram chat using a bot."""

    # Default emoji mapping for different log levels
    DEFAULT_LEVEL_EMOJI = {
        logging.DEBUG: '🔍',
        logging.INFO: 'ℹ️',
        logging.WARNING: '⚠️',
        logging.ERROR: '❌',
        logging.CRITICAL: '🚨',
    }

    def __init__(
        self,
        token: str,
        chat_ids: Union[str, int, List[Union[str, int]]],
        level: int = logging.NOTSET,
        fmt: Optional[str] = None,
        parse_mode: Optional[str] = 'HTML',
        batch_size: int = 1,
        batch_interval: float = 1.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        project_name: Optional[str] = None,
        project_emoji: str = '🔷',
        add_hashtags: bool = True,
        message_format: Optional[Callable[[logging.LogRecord, Dict[str, Any]], str]] = None,
        level_emojis: Optional[Dict[int, str]] = None,
        include_project_name: bool = True,
        include_level_emoji: bool = True,
        datefmt: Optional[str] = None,
        test_mode: bool = False
    ):
        """Initialize the handler."""
        super().__init__(level)
        self.token = token
        self.chat_ids = [chat_ids] if isinstance(chat_ids, (str, int)) else chat_ids
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
        self.fmt = fmt

        # Initialize bot
        self._bot = Bot(token=token)
        
        # Shutdown flags
        self._is_shutting_down = threading.Event()
        self._shutdown_complete = threading.Event()

        # Set formatter with custom date format
        if fmt is not None:
            self.formatter = logging.Formatter(fmt, datefmt=self.datefmt)
        else:
            self.formatter = logging.Formatter('%(message)s', datefmt=self.datefmt)

        # Create time formatter
        self.time_formatter = logging.Formatter(datefmt=self.datefmt) if self.datefmt else None

        # Initialize batching
        self.message_queue: Dict[str, Queue] = defaultdict(Queue)
        self.batch_lock = Lock()
        self.batch_event = Event()
        self._closed = False

        # Rate limiting state
        self.last_message_time = 0
        self.min_message_interval = 1

        # Create event loop in a separate thread if not in test mode
        if not test_mode:
            self.executor: Optional[ThreadPoolExecutor] = ThreadPoolExecutor(max_workers=1)
            self.loop = asyncio.new_event_loop()
            if self.executor:
                self.executor.submit(self._run_event_loop)

            # Start batch sender thread
            self.batch_thread: Optional[Thread] = Thread(target=self._batch_sender, daemon=True)
            if self.batch_thread:
                self.batch_thread.start()

            # Setup signal handlers
            self._setup_signal_handlers()
        else:
            # In test mode, use the current event loop
            self.loop = asyncio.get_event_loop()
            self.executor = None
            self.batch_thread = None

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum: int, frame: Any) -> None:
            # Log signal received
            print(f"Received signal {signum}, initiating graceful shutdown...", 
                  file=sys.stderr)
            
            # Initiate shutdown
            self._initiate_shutdown()

        # Register handlers for common signals
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            try:
                signal.signal(sig, signal_handler)
            except ValueError as e:
                # Log if we can't set signal handler (e.g., in a thread)
                print(f"Could not set handler for signal {sig}: {e}", 
                      file=sys.stderr)

    def _initiate_shutdown(self) -> None:
        """Initiate graceful shutdown process."""
        if not self._is_shutting_down.is_set():
            self._is_shutting_down.set()
            try:
                # Run shutdown in the event loop
                if hasattr(self, 'loop') and self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self._shutdown(), self.loop
                    )
            except Exception as e:
                print(f"Error during shutdown initiation: {e}", 
                      file=sys.stderr)

    async def _shutdown(self) -> None:
        """Perform graceful shutdown."""
        try:
            # Flush remaining messages
            await self._flush_all_queues()

            # Close bot session
            if self._bot:
                try:
                    await self._bot.close()
                except Exception as e:
                    print(f"Error closing bot session: {e}", 
                          file=sys.stderr)

            # Stop event loop
            if hasattr(self, 'loop') and self.loop:
                self.loop.stop()

            # Clean up executor
            if self.executor:
                self.executor.shutdown(wait=True)

            self._shutdown_complete.set()
        except Exception as e:
            print(f"Error during shutdown: {e}", 
                  file=sys.stderr)

    async def _flush_all_queues(self) -> None:
        """Flush all message queues."""
        try:
            async with self.batch_lock:
                for chat_id in self.chat_ids:
                    queue = self.message_queue[chat_id]
                    while not queue.empty():
                        messages = []
                        try:
                            while not queue.empty() and len(messages) < self.batch_size:
                                messages.append(queue.get_nowait())
                        except Exception:
                            break

                        if messages:
                            try:
                                await self._send_batch(chat_id, messages)
                            except Exception as e:
                                print(f"Error sending final batch to {chat_id}: {e}", 
                                      file=sys.stderr)
        except Exception as e:
            print(f"Error flushing queues: {e}", 
                  file=sys.stderr)

    async def close(self) -> None:
        """Close the handler and clean up resources."""
        if self._closed:
            return

        self._closed = True
        self._is_shutting_down.set()

        try:
            # Wait for shutdown to complete with timeout
            shutdown_task = asyncio.create_task(self._shutdown())
            try:
                await asyncio.wait_for(shutdown_task, timeout=SHUTDOWN_TIMEOUT)
            except asyncio.TimeoutError:
                print("Shutdown timed out", file=sys.stderr)

        except Exception as e:
            print(f"Error during handler close: {e}", 
                  file=sys.stderr)
        finally:
            # Ensure parent class close is called
            super().close()

    def __del__(self) -> None:
        """Ensure resources are cleaned up."""
        if not self._closed:
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(self.close())
                )
            else:
                asyncio.run(self.close())

    def _get_bot(self) -> Bot:
        """Get the bot instance."""
        return self._bot

    def default_message_format(self, record: logging.LogRecord, context: Dict[str, Any]) -> str:
        """Default message formatting function."""
        parts = []

        # Add project name if enabled
        if self.include_project_name and self.project_name:
            parts.append(f"{self.project_emoji} <b>[{self.project_name}]</b>")

        # Add level emoji if enabled
        if self.include_level_emoji:
            level_emoji = self.level_emojis.get(record.levelno, '🔵')
            parts.append(level_emoji)

        # Add level name and timestamp
        parts.append(f"<b>[{record.levelname}]</b>")

        # Format timestamp using custom formatter if datefmt is provided
        if context.get('datefmt'):
            timestamp_formatter = logging.Formatter(datefmt=context['datefmt'])
            timestamp = timestamp_formatter.formatTime(record)
        else:
            timestamp = self.formatter.formatTime(record)
        parts.append(f"[{timestamp}]")

        # Add the message
        message = self.formatter.format(record)
        parts.append(f"\n{message}")

        # Add exception info if present
        if record.exc_info:
            if isinstance(record.exc_info, tuple):
                exc_text = self.formatter.formatException(record.exc_info)
            else:
                exc_info = sys.exc_info()
                exc_text = (
                    self.formatter.formatException(exc_info)
                    if exc_info != (None, None, None) else None
                )

            if exc_text:
                parts.append(f"\n<code>{exc_text}</code>")

        # Add hashtags if enabled
        if self.add_hashtags and self.project_name:
            hashtags = [f"#{self.project_name.replace(' ', '_')}"]
            if record.levelname:
                hashtags.append(f"#{record.levelname.lower()}")
            parts.append('\n\n' + ' '.join(hashtags))

        return ' '.join(parts)

    def format_time(self, record: logging.LogRecord) -> str:
        """Format time using custom formatter or default."""
        if self.time_formatter:
            return self.time_formatter.formatTime(record)
        return self.formatter.formatTime(record)

    def _format_message(self, record: logging.LogRecord) -> str:
        """Format message using custom or default formatter."""
        context = {
            'project_name': self.project_name,
            'project_emoji': self.project_emoji,
            'level_emojis': self.level_emojis,
            'parse_mode': self.parse_mode,
            'formatter': self.formatter,
            'time_formatter': self.time_formatter,
            'format_time': lambda: self.format_time(record),
            'datefmt': self.datefmt
        }

        if self.message_format:
            msg = self.message_format(record, context)
        else:
            msg = self.default_message_format(record, context)

        if self.parse_mode == 'MarkdownV2':
            # Escape special characters for MarkdownV2
            special_chars = [
                '_', '*', '[', ']', '(', ')', '~', '`', '>', '#',
                '+', '-', '=', '|', '{', '}', '.', '!'
            ]
            for char in special_chars:
                msg = msg.replace(char, f'\\{char}')

        return msg

    def _run_event_loop(self) -> None:
        """Run event loop in a separate thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _split_message(self, message: str) -> List[str]:
        """Split message into chunks that fit Telegram's message size limit."""
        max_length = 4096
        chunks = []

        while message:
            if len(message) <= max_length:
                chunks.append(message)
                break

            # Try to split at newline
            split_idx = message[:max_length].rfind('\n')
            if split_idx == -1:
                # No newline found, split at max_length
                split_idx = max_length

            chunks.append(message[:split_idx])
            message = message[split_idx:].lstrip()

        return chunks

    async def _send_message_async(self, chat_id: str, message: str) -> None:
        """Send a message to a Telegram chat."""
        bot = self._get_bot()
        chunks = self._split_message(message)

        for chunk in chunks:
            if self.test_mode:
                # In test mode, just call the mock without error handling
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=chunk,
                        parse_mode=self.parse_mode
                    )
                except (InvalidToken, TelegramError) as e:
                    # In test mode, print error and continue
                    print(f"Failed to send log to Telegram chat {chat_id}: {str(e)}")
                    # Don't raise the error in test mode
                    return
            else:
                # In normal mode, handle errors and retries
                retries = 0
                while retries <= self.max_retries:
                    try:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=chunk,
                            parse_mode=self.parse_mode
                        )
                        break
                    except (RetryAfter, TimedOut) as e:
                        if isinstance(e, RetryAfter):
                            await asyncio.sleep(e.retry_after)
                        else:
                            await asyncio.sleep(self.retry_delay)
                        retries += 1
                    except TelegramError as e:
                        if retries >= self.max_retries:
                            print(
                                f"Failed to send log to Telegram chat {chat_id} "
                                f"after {retries} retries: {str(e)}"
                            )
                            break
                        await asyncio.sleep(self.retry_delay)
                        retries += 1

            # Rate limiting between chunks
            if len(chunks) > 1:
                await asyncio.sleep(self.min_message_interval)

    def _batch_sender(self) -> None:
        """Background task to periodically flush queues."""
        while not self._closed and not self._is_shutting_down.is_set():
            try:
                # Wait for batch interval or event
                self.batch_event.wait(timeout=self.batch_interval)
                self.batch_event.clear()
                
                # Skip if shutting down
                if self._is_shutting_down.is_set():
                    break
                    
                # Flush all queues
                for chat_id in self.chat_ids:
                    if self.message_queue[chat_id].qsize() > 0:
                        asyncio.run_coroutine_threadsafe(
                            self._flush_queue(chat_id), 
                            self.loop
                        )
                        
            except Exception as e:
                print(f"Error in batch sender: {e}", 
                      file=sys.stderr)
                
        # Final flush on shutdown
        if self._is_shutting_down.is_set():
            try:
                asyncio.run_coroutine_threadsafe(
                    self._flush_all_queues(), 
                    self.loop
                ).result(timeout=FLUSH_TIMEOUT)
            except Exception as e:
                print(f"Error in final flush: {e}", 
                      file=sys.stderr)

    async def emit(self, record: logging.LogRecord) -> None:
        """Emit a record.

        Format the record and put it in the batch queue.
        When the queue reaches batch_size, trigger a send.
        """
        if self._closed or self._is_shutting_down.is_set():
            return

        try:
            msg = self._format_message(record)
            
            # Split message if it's too long
            messages = self._split_message(msg)
            
            for chat_id in self.chat_ids:
                for message_part in messages:
                    await self._add_to_queue(chat_id, message_part)
                    
        except Exception as e:
            print(f"Error in emit: {e}", file=sys.stderr)
            self.handleError(record)

    async def _add_to_queue(self, chat_id: Union[str, int], message: str) -> None:
        """Add message to queue and flush if needed."""
        try:
            async with self.batch_lock:
                queue = self.message_queue[chat_id]
                queue.put_nowait(message)
                
                # Check if we need to flush
                if queue.qsize() >= self.batch_size:
                    await self._flush_queue(chat_id)
                    
        except Exception as e:
            print(f"Error adding message to queue for {chat_id}: {e}", 
                  file=sys.stderr)

    async def _flush_queue(self, chat_id: Union[str, int]) -> None:
        """Flush queue for specific chat_id."""
        try:
            async with self.batch_lock:
                queue = self.message_queue[chat_id]
                messages = []
                
                # Get all messages from queue
                while not queue.empty() and len(messages) < self.batch_size:
                    try:
                        messages.append(queue.get_nowait())
                    except Exception:
                        break
                        
                if messages:
                    await self._send_batch(chat_id, messages)
                    
        except Exception as e:
            print(f"Error flushing queue for {chat_id}: {e}", 
                  file=sys.stderr)

    async def _send_batch(self, chat_id: Union[str, int], messages: List[str]) -> None:
        """Send a batch of messages with retries."""
        if not messages:
            return
            
        message = '\n\n'.join(messages)
        retry_count = 0
        
        while retry_count <= self.max_retries:
            try:
                # Rate limiting
                now = time.time()
                if now - self.last_message_time < self.min_message_interval:
                    await asyncio.sleep(self.min_message_interval)
                
                # Send message
                await self._bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=self.parse_mode
                )
                self.last_message_time = time.time()
                return
                
            except RetryAfter as e:
                # Handle rate limiting
                await asyncio.sleep(e.retry_after)
                
            except TimedOut:
                # Handle timeouts
                await asyncio.sleep(self.retry_delay)
                
            except Exception as e:
                print(f"Error sending batch to {chat_id} (attempt {retry_count + 1}/{self.max_retries + 1}): {e}", 
                      file=sys.stderr)
                if retry_count == self.max_retries:
                    break
                await asyncio.sleep(self.retry_delay)
                
            retry_count += 1

    async def __aenter__(self) -> 'TelegramHandler':
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[Exception], 
                        exc_tb: Optional[Any]) -> None:
        """Async context manager exit."""
        await self.close()
        
        # Log any errors that occurred
        if exc_type is not None:
            print(f"Error during context exit: {exc_val}", 
                  file=sys.stderr)