import logging
import time
import sys
from tgbot_logging import TelegramHandler

def test_all_features():
    # Create logger
    logger = logging.getLogger('TestLogger')
    logger.setLevel(logging.DEBUG)
    
    # Add console output for comparison
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create Telegram handler with project details
    telegram_handler = TelegramHandler(
        token='YOUR_BOT_TOKEN',  # Replace with your bot token
        chat_ids=['YOUR_CHAT_ID'],  # Replace with your chat ID
        level=logging.INFO,
        parse_mode='HTML',
        batch_size=5,  # Group by 5 messages
        batch_interval=3.0,  # Send every 3 seconds
        max_retries=3,
        retry_delay=2.0,
        project_name='MyTestProject',  # Project name
        project_emoji='🚀',  # Project emoji
        add_hashtags=True  # Add hashtags
    )
    logger.addHandler(telegram_handler)
    
    try:
        # 1. Test different logging levels
        logger.debug('This is a debug message (should not be sent to Telegram)')
        logger.info('This is an info message')
        time.sleep(1)
        
        logger.warning('This is a warning message')
        time.sleep(1)
        
        logger.error('This is an error message')
        time.sleep(1)
        
        # 2. Test HTML formatting
        logger.info('Message with <b>bold text</b>, <i>italic</i> and <code>monospace font</code>')
        time.sleep(2)
        
        # 3. Test batching
        logger.info('Starting batch test...')
        for i in range(5):
            logger.info(f'Batch test message {i + 1}')
            time.sleep(0.5)
        
        time.sleep(3)
        
        # 4. Test error handling
        logger.info('Testing exception handling...')
        try:
            raise ValueError('This is a test error!')
        except Exception as e:
            logger.exception('An error occurred:')
        
        time.sleep(2)
        
        # 5. Test long messages
        logger.info('Testing long message:\n' + '-' * 50 + '\n' + 
                   'This is a very long message that should be properly formatted.\n' +
                   'Testing line breaks and general formatting.\n' + '-' * 50)
        
        # Wait for all messages to be sent
        logger.info('Tests completed! Waiting for all messages to be sent...')
        time.sleep(5)
        
    finally:
        # Properly close handlers
        telegram_handler.close()
        console_handler.close()
        time.sleep(2)

def test_multiple_projects():
    """Demonstration of using different projects."""
    # Create loggers for different projects
    projects = {
        'Frontend': ('💻', logging.getLogger('Frontend')),
        'Backend': ('⚙️', logging.getLogger('Backend')),
        'Database': ('🗄️', logging.getLogger('Database'))
    }
    
    # Configure loggers
    for project_name, (emoji, logger) in projects.items():
        logger.setLevel(logging.INFO)
        
        # Create handler for each project
        handler = TelegramHandler(
            token='YOUR_BOT_TOKEN',  # Replace with your bot token
            chat_ids=['YOUR_CHAT_ID'],  # Replace with your chat ID
            level=logging.INFO,
            project_name=project_name,
            project_emoji=emoji,
            batch_size=2,
            batch_interval=1.0
        )
        logger.addHandler(handler)
    
    try:
        # Simulate logs from different projects
        projects['Frontend'][1].info('User logged in')
        projects['Backend'][1].warning('High API load')
        projects['Database'][1].error('Replica connection error')
        
        time.sleep(2)
        
        projects['Frontend'][1].info('New order created')
        projects['Backend'][1].info('Order processed')
        projects['Database'][1].info('Transaction completed')
        
        # Wait for all messages to be sent
        time.sleep(5)
        
    finally:
        # Close all handlers
        for _, (_, logger) in projects.items():
            for handler in logger.handlers:
                handler.close()
        time.sleep(2)

if __name__ == '__main__':
    print('🚀 Starting tests...\n')
    print('1. Testing basic functionality...')
    test_all_features()
    print('\n2. Testing work with different projects...')
    test_multiple_projects()
    print('\n✨ Testing completed!') 