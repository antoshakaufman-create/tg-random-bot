from aiogram import Router, Bot
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
import asyncio
import os

from bot.handlers.states import TaskStates
from bot.database import (
    update_participant,
    get_next_participant_number,
    increment_daily_stats,
    get_or_create_participant,
    get_participant_by_phone
)
from bot.utils import check_win
from bot.config import EXEED_CHANNEL_URL

router = Router()


async def show_slot_animation(callback: CallbackQuery):
    """Show slot machine animation effect."""
    frames = [
        "🎰 Крутим барабан...\n\n[ 🎁 | 🎁 | 🎁 ]",
        "🎰 Крутим барабан...\n\n[ 🎄 | 🎁 | 🎁 ]",
        "🎰 Крутим барабан...\n\n[ 🎄 | 🎄 | 🎁 ]",
        "🎰 Крутим барабан...\n\n[ 🎄 | 🎄 | 🎄 ]",
        "🎰 Крутим барабан...\n\n[ ⭐ | 🎄 | 🎄 ]",
        "🎰 Крутим барабан...\n\n[ ⭐ | ⭐ | 🎄 ]",
        "🎰 Крутим барабан...\n\n[ ⭐ | ⭐ | ⭐ ]",
        "🎰 Определяем результат...\n\n[ 🔄 | 🔄 | 🔄 ]",
    ]
    
    for frame in frames:
        try:
            await callback.message.edit_text(frame)
            await asyncio.sleep(0.4)
        except Exception:
            pass


@router.callback_query(lambda c: c.data == "get_result")
async def get_result_callback(callback: CallbackQuery, state: FSMContext):
    """Handle get result button - the main prize draw moment."""
    current_state = await state.get_state()
    
    if current_state != TaskStates.ready_for_result:
        await callback.answer("❌ Пожалуйста, сначала выполните все задания!", show_alert=True)
        return
    
    # Get participant data
    participant = await get_or_create_participant(callback.from_user.id)
    existing_number = participant.get("participant_number")
    existing_prize = participant.get("prize")
    existing_prize_type = participant.get("prize_type")  # Only set after actual participation
    
    # --- DUPLICATE CHECK BY TELEGRAM ID ---
    # Check prize_type because is_winner might be 0 by default
    if existing_number and existing_prize_type is not None:

        # User already participated - show their existing result
        if participant.get("is_winner"):
            # Send photo with win reminder
            brand_zone_photo = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "brand_zone.jpg")
            
            # Show prize type for duplicate winners
            existing_prize_type = participant.get("prize_type")
            if existing_prize_type == "big":
                prize_text = "🎁 ПОДАРОЧНЫЙ НАБОР от EXEED!"
            else:
                prize_text = "🔑 Фирменный брелок от EXEED!"
            
            win_caption = (
                f"Вы уже участвовали!\n"
                f"Ваш номер: {existing_number} 🎉\n\n"
                f"Вы выиграли:\n"
                f"{prize_text}\n\n"
                f"Чтобы получить подарок, подойдите на бренд-зону EXEED возле павильона №1 и назовите свой номер участника."
            )
            
            await callback.message.delete()
            
            if os.path.exists(brand_zone_photo):
                await callback.message.answer_photo(
                    photo=FSInputFile(brand_zone_photo),
                    caption=win_caption
                )
            else:
                await callback.message.answer(win_caption)
        else:
            await callback.message.edit_text(
                f"Вы уже участвовали!\n"
                f"Ваш номер: {existing_number}\n"
                f"К сожалению, в этот раз без призов.\n\n"
                f"Но не расстраивайтесь — впереди ещё много активностей от EXEED!\n"
                f"Следите за новостями в @exeedrussia."
            )
        await state.clear()
        return
    
    # --- DUPLICATE CHECK BY PHONE NUMBER ---
    phone = participant.get("phone")
    if phone:
        phone_duplicate = await get_participant_by_phone(phone)
        if phone_duplicate and phone_duplicate.get("telegram_id") != callback.from_user.id:
            # Someone with this phone already participated
            dup_number = phone_duplicate.get("participant_number")
            dup_winner = phone_duplicate.get("is_winner")
            
            if dup_winner:
                brand_zone_photo = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "brand_zone.jpg")
                
                win_caption = (
                    f"Этот номер телефона уже участвовал!\n"
                    f"Номер участника: {dup_number} 🎉\n\n"
                    f"Вы выиграли приз от EXEED — фирменный мерч.\n"
                    f"Чтобы получить подарок, подойдите на бренд-зону EXEED возле павильона №1 и назовите свой номер участника."
                )
                
                await callback.message.delete()
                
                if os.path.exists(brand_zone_photo):
                    await callback.message.answer_photo(
                        photo=FSInputFile(brand_zone_photo),
                        caption=win_caption
                    )
                else:
                    await callback.message.answer(win_caption)
            else:
                await callback.message.edit_text(
                    f"Этот номер телефона уже участвовал!\n"
                    f"Номер участника: {dup_number}\n"
                    f"К сожалению, в этот раз без призов.\n\n"
                    f"Но не расстраивайтесь — впереди ещё много активностей от EXEED!\n"
                    f"Следите за новостями в @exeedrussia."
                )
            await state.clear()
            return
    
    # --- NEW PARTICIPANT ---
    # Show slot machine animation
    await show_slot_animation(callback)
    
    # Get new participant number
    participant_number = existing_number or await get_next_participant_number()
    
    # Check if winner
    is_winner, prize, prize_type = await check_win()
    
    # Update participant record
    await update_participant(
        callback.from_user.id,
        participant_number=participant_number,
        is_winner=is_winner,
        prize=prize,
        prize_type=prize_type
    )
    
    # Update daily stats
    await increment_daily_stats(
        small_prizes=1 if prize_type == "small" else 0,
        big_prizes=1 if prize_type == "big" else 0,
        participants=1
    )
    
    if is_winner:
        # Send photo of brand zone with win message
        brand_zone_photo = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "brand_zone.jpg")
        
        # Different message for big vs small prize
        if prize_type == "big":
            prize_text = "🎁 ПОДАРОЧНЫЙ НАБОР от EXEED!"
        else:
            prize_text = "🔑 Фирменный брелок от EXEED!"
        
        win_caption = (
            f"Спасибо за участие!\n"
            f"Ваш номер: {participant_number} 🎉\n\n"
            f"Поздравляем! Вы выиграли:\n"
            f"{prize_text}\n\n"
            f"Чтобы получить подарок, подойдите на бренд-зону EXEED возле павильона №1 и назовите свой номер участника.\n\n"
            f"Хорошего отдыха и с наступающим!"
        )
        
        await callback.message.delete()
        
        if os.path.exists(brand_zone_photo):
            await callback.message.answer_photo(
                photo=FSInputFile(brand_zone_photo),
                caption=win_caption
            )
        else:
            await callback.message.answer(win_caption)
    else:
        await callback.message.edit_text(
            f"Спасибо за участие!\n"
            f"Ваш номер: {participant_number}\n"
            f"К сожалению, в этот раз без призов.\n\n"
            f"Но не расстраивайтесь — впереди ещё много активностей от EXEED!\n"
            f"Следите за новостями в @exeedrussia.\n"
            f"Хорошего отдыха и с наступающим!"
        )
    
    await state.clear()

