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


ADMIN_ID = 802692559


@router.message(Command("reset_me"))
async def reset_me(message: types.Message):
    """Reset admin's participation status for testing."""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Команда доступна только администратору.")
        return
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # First, check current state
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM participants WHERE telegram_id = ?",
                (message.from_user.id,)
            )
            before = await cursor.fetchone()
            
            # Reset the record
            await db.execute(
                """UPDATE participants 
                   SET participant_number = NULL, 
                       is_winner = NULL, 
                       prize = NULL, 
                       prize_type = NULL,
                       photo_path = NULL
                   WHERE telegram_id = ?""",
                (message.from_user.id,)
            )
            await db.commit()
            
            # Verify reset
            cursor = await db.execute(
                "SELECT participant_number, is_winner FROM participants WHERE telegram_id = ?",
                (message.from_user.id,)
            )
            after = await cursor.fetchone()
        
        before_info = f"До: номер={before['participant_number']}, winner={before['is_winner']}" if before else "До: не найден"
        after_info = f"После: номер={after['participant_number'] if after else 'N/A'}, winner={after['is_winner'] if after else 'N/A'}"
        
        await message.answer(
            f"✅ <b>Статус сброшен!</b>\n\n"
            f"<code>{before_info}\n{after_info}</code>\n\n"
            f"Отправьте /start и пройдите путь заново.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("reset_all"))
async def reset_all(message: types.Message):
    """Clear entire database - all participants and stats."""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Команда доступна только администратору.")
        return
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Count before
            cursor = await db.execute("SELECT COUNT(*) FROM participants")
            count = (await cursor.fetchone())[0]
            
            # Delete all
            await db.execute("DELETE FROM participants")
            await db.execute("DELETE FROM daily_stats")
            await db.commit()
        
        await message.answer(
            f"🗑 <b>База данных очищена!</b>\n\n"
            f"Удалено записей: {count}\n\n"
            f"Все участники и статистика сброшены.\n"
            f"Отправьте /start для тестирования.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Reset all failed: {e}")
        await message.answer(f"❌ Ошибка: {e}")



