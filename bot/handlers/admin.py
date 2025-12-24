import csv
import io
import logging
from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

from bot.config import DATABASE_PATH
import aiosqlite

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("export"))
async def export_database(message: types.Message):
    """Export participants database to CSV."""
    logger.info(f"Export requested by user {message.from_user.id}")
    
    # Security check: Only allow specific admin
    ADMIN_ID = 802692559
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ У вас нет прав для выполнения этой команды.")
        return

    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM participants")
            rows = await cursor.fetchall()

            if not rows:
                await message.answer("📁 База данных пуста.")
                return

            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            if rows:
                writer.writerow(rows[0].keys())

            # Write data
            for row in rows:
                writer.writerow(list(row))

            # Prepare file for sending
            output.seek(0)
            document = BufferedInputFile(
                output.getvalue().encode(), 
                filename=f"participants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

            await message.reply_document(
                document,
                caption=f"📁 Экспорт базы данных\nКоличество записей: {len(rows)}"
            )

    except Exception as e:
        logger.error(f"Export failed: {e}")
        await message.answer(f"❌ Ошибка экспорта: {e}")
