import logging
import time
from tgbot_logging import TelegramHandler

def setup_logger():
    # Create logger
    logger = logging.getLogger('MyApp')
    logger.setLevel(logging.DEBUG)

    # Create TelegramHandler with advanced features
    telegram_handler = TelegramHandler(
        token='YOUR_BOT_TOKEN',  # Replace with your bot token
        chat_ids=['YOUR_CHAT_ID'],  # Replace with your chat ID
        level=logging.INFO,
        parse_mode='HTML',  # Support for HTML formatting
        batch_size=5,  # Batch 5 messages together
        batch_interval=2.0,  # Send batch every 2 seconds or when full
        max_retries=3,  # Retry failed messages 3 times
        retry_delay=1.0,  # Wait 1 second between retries
        fmt='<b>%(levelname)s</b> [%(asctime)s]\n%(message)s'  # Custom HTML format
    )

    # Add handler to logger
    logger.addHandler(telegram_handler)
    return logger

def main():
    logger = setup_logger()
    
    # Basic logging examples
    logger.debug('This is a debug message (won\'t be sent to Telegram)')
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    
    # HTML formatting example
    logger.info('Message with <b>bold text</b> and <i>italic text</i>')
    
    # Batching example
    for i in range(10):
        logger.info(f'Batch message {i + 1}')
        time.sleep(0.1)  # Small delay to simulate real work
    
    # Error with traceback
    try:
        # Simulate an error
        result = 1 / 0
    except Exception as e:
        logger.exception('An error occurred:')
    
    # Keep the program running to allow batched messages to be sent
    time.sleep(3)

if __name__ == '__main__':
    main() 