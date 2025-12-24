from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import asyncio

from bot.handlers.states import TaskStates
from bot.database import (
    update_participant,
    get_next_participant_number,
    increment_daily_stats,
    get_or_create_participant
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
    
    # --- DUPLICATE CHECK ---
    # Check prize_type because is_winner might be 0 by default
    if existing_number and existing_prize_type is not None:

        # User already participated - show their existing result
        if participant.get("is_winner"):
            prize_type = participant.get("prize_type", "small")
            emoji = "🎉🎉🎉" if prize_type == "big" else "🎁"
            prize_label = "БОЛЬШОЙ ПРИЗ" if prize_type == "big" else "Приз"
            
            await callback.message.edit_text(
                f"⚠️ <b>Вы уже участвовали!</b>\n\n"
                f"🎟 Ваш номер: <b>#{existing_number}</b>\n\n"
                f"{emoji} <b>{prize_label}: {existing_prize}!</b>\n\n"
                f"📍 Покажите это сообщение промоутеру.",
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                f"⚠️ <b>Вы уже участвовали!</b>\n\n"
                f"🎟 Ваш номер: <b>#{existing_number}</b>\n\n"
                f"К сожалению, приз не выпал.\n\n"
                f"🎁 Вы участвуете в главном розыгрыше 10 января!\n\n"
                f"📢 Следите за новостями: {EXEED_CHANNEL_URL}",
                parse_mode="HTML"
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
        if prize_type == "big":
            emoji = "🎉🎉🎉"
            prize_label = "БОЛЬШОЙ ПРИЗ"
        else:
            emoji = "🎁"
            prize_label = "Приз"
        
        await callback.message.edit_text(
            f"{emoji} <b>ПОЗДРАВЛЯЕМ!</b> {emoji}\n\n"
            f"🎟 Ваш номер участника: <b>#{participant_number}</b>\n\n"
            f"🏆 <b>{prize_label}: {prize}!</b>\n\n"
            f"📍 Покажите это сообщение промоутеру на стойке, чтобы забрать приз.",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"🎟 <b>Спасибо за участие!</b>\n\n"
            f"Ваш номер участника: <b>#{participant_number}</b>\n\n"
            f"К сожалению, приз не выпал. Но не расстраивайтесь!\n\n"
            f"🎁 <b>Вы участвуете в главном розыгрыше iPhone и велосипеда 10 января!</b>\n\n"
            f"📢 Следите за новостями: {EXEED_CHANNEL_URL}",
            parse_mode="HTML"
        )
    
    await state.clear()

