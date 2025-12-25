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


from aiogram import Bot
from bot.config import EXEED_CHANNEL_ID, LUZHNIKI_CHANNEL_ID


@router.message(Command("check_channels"))
async def check_channels(message: types.Message, bot: Bot):
    """Check if bot is admin in required channels."""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Команда доступна только администратору.")
        return
    
    results = []
    
    for channel_id, name in [(EXEED_CHANNEL_ID, "EXEED"), (LUZHNIKI_CHANNEL_ID, "Лужники")]:
        try:
            # Get bot's own info
            me = await bot.get_me()
            # Try to get bot's membership in channel
            member = await bot.get_chat_member(chat_id=channel_id, user_id=me.id)
            
            if member.status in ["administrator", "creator"]:
                results.append(f"✅ {name}: Бот — администратор")
            elif member.status == "member":
                results.append(f"⚠️ {name}: Бот — участник (не админ!)")
            else:
                results.append(f"❌ {name}: Статус — {member.status}")
        except Exception as e:
            results.append(f"❌ {name}: Ошибка — {str(e)[:50]}")
    
    await message.answer(
        f"<b>Статус бота в каналах:</b>\n\n" + "\n".join(results),
        parse_mode="HTML"
    )


@router.message(Command("check_subs"))
async def check_subs(message: types.Message, bot: Bot):
    """Check if all DB participants are subscribed to EXEED channel."""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Команда доступна только администратору.")
        return
    
    await message.answer("⏳ Проверяю подписки участников...")
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT telegram_id, name FROM participants")
            rows = await cursor.fetchall()
        
        if not rows:
            await message.answer("📁 База данных пуста.")
            return
        
        subscribed = 0
        not_subscribed = 0
        errors = 0
        not_sub_list = []
        
        from aiogram.enums import ChatMemberStatus
        
        for row in rows:
            try:
                member = await bot.get_chat_member(
                    chat_id=EXEED_CHANNEL_ID, 
                    user_id=row["telegram_id"]
                )
                if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                    subscribed += 1
                else:
                    not_subscribed += 1
                    not_sub_list.append(f"{row['name']} (ID: {row['telegram_id']})")
            except Exception:
                errors += 1
        
        # Prepare not subscribed list (max 10)
        not_sub_text = ""
        if not_sub_list:
            not_sub_text = "\n\n<b>Не подписаны:</b>\n" + "\n".join(not_sub_list[:10])
            if len(not_sub_list) > 10:
                not_sub_text += f"\n... и ещё {len(not_sub_list) - 10}"
        
        await message.answer(
            f"<b>Проверка подписок на EXEED:</b>\n\n"
            f"✅ Подписаны: {subscribed}\n"
            f"❌ Не подписаны: {not_subscribed}\n"
            f"⚠️ Ошибки: {errors}\n"
            f"📊 Всего: {len(rows)}"
            f"{not_sub_text}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

