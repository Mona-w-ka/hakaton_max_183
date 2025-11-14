import asyncio
import logging
from BOT import BOT
from config import token

logging.basicConfig(level=logging.INFO)

async def main():
    bot = BOT(token)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())