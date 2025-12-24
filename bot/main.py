import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from bot.config import BOT_TOKEN
from bot.database import init_db
from bot.handlers import setup_routers


async def handle_health_check(request):
    """Simple health check endpoint."""
    return web.Response(text="OK", status=200)


async def start_health_check_server():
    """Start a background HTTP server for Render health checks."""
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Get port from environment or use 10000 by default (standard for Render)
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    logging.info(f"Health check server starting on port {port}...")
    await site.start()
    
    # Keep it running
    while True:
        await asyncio.sleep(3600)


async def main():
    """Main entry point for the bot."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )
    logger = logging.getLogger(__name__)
    
    # Check token
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set! Please configure .env file.")
        sys.exit(1)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # ONE-TIME CLEANUP - REMOVE AFTER TESTING
    import aiosqlite
    from bot.config import DATABASE_PATH
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM participants")
        await db.execute("DELETE FROM daily_stats")
        await db.commit()
    logger.info("🗑 DATABASE CLEARED ON STARTUP")


    from bot.config import STORAGE_CHANNEL_ID
    logger.info(f"Configured STORAGE_CHANNEL_ID: '{STORAGE_CHANNEL_ID}'")
    
    # Create bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    
    # Setup routers
    main_router = setup_routers()
    dp.include_router(main_router)
    
    logger.info("Bot starting...")
    
    # Start health check server and bot polling concurrently
    try:
        await asyncio.gather(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
            start_health_check_server()
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
