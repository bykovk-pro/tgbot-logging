import asyncio
from telegram import Bot
from telegram.error import RetryAfter

async def test_bot():
    bot = Bot('YOUR_BOT_TOKEN')
    try:
        # Get bot information
        me = await bot.get_me()
        print(f"Bot info: {me.first_name} (@{me.username})")
        
        # Send test message
        message = await bot.send_message(
            chat_id='YOUR_CHAT_ID',
            text='🔥 Test message!\nIf you see this, the bot is working correctly.'
        )
        print(f"Message sent successfully: {message.message_id}")
        
        # Wait before closing bot
        await asyncio.sleep(2)
        
    except RetryAfter as e:
        print(f"Rate limit exceeded. Need to wait {e.retry_after} seconds")
        # Wait specified time and try again
        await asyncio.sleep(e.retry_after)
        return await test_bot()
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        try:
            # Try to close bot, ignoring errors
            await bot.close()
        except Exception as e:
            print(f"Warning: Could not close bot properly: {str(e)}")

if __name__ == '__main__':
    asyncio.run(test_bot()) 