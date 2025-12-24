from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.handlers.states import TaskStates
from bot.database import (
    update_participant,
    get_next_participant_number,
    increment_daily_stats
)
from bot.utils import check_win
from bot.config import EXEED_CHANNEL_URL

router = Router()


@router.callback_query(lambda c: c.data == "get_result")
async def get_result_callback(callback: CallbackQuery, state: FSMContext):
    """Handle get result button - the main prize draw moment."""
    current_state = await state.get_state()
    
    if current_state != TaskStates.ready_for_result:
        await callback.answer("❌ Пожалуйста, сначала выполните все задания!", show_alert=True)
        return
    
    # Get participant data to retrieve assigned number
    from bot.database import get_or_create_participant
    participant = await get_or_create_participant(callback.from_user.id)
    participant_number = participant.get("participant_number")
    
    # Fallback if for some reason number is missing (should not happen in normal flow)
    if not participant_number:
        participant_number = await get_next_participant_number()
    
    # Check if winner (returns is_winner, prize, prize_type)
    is_winner, prize, prize_type = await check_win()
    
    # Update participant record (only win status)
    await update_participant(
        callback.from_user.id,
        participant_number=participant_number, # ensure it's saved/kept
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
        # Different message for big vs small prize
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
