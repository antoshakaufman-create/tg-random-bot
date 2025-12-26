from aiogram import Router, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatMemberStatus

from bot.handlers.states import TaskStates
from bot.keyboards import get_subscription_keyboard
from bot.config import EXEED_CHANNEL_ID, LUZHNIKI_CHANNEL_ID

router = Router()


async def check_user_subscription(bot: Bot, user_id: int, channel_id: str) -> bool:
    """Check if user is subscribed to a channel."""
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        ]
    except Exception:
        # If we can't check (bot not admin or channel doesn't exist), assume subscribed
        return True


@router.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle subscription check button."""
    user_id = callback.from_user.id
    
    # Check only EXEED channel (Лужники doesn't allow member list access)
    exeed_subscribed = await check_user_subscription(bot, user_id, EXEED_CHANNEL_ID)
    
    if exeed_subscribed:
        # User is subscribed
        await callback.message.edit_text(
            "🎉 Супер! Осталось последнее:\n\n"
            "📸 Сделайте классное фото на катке и отправьте его сюда!"
        )
        
        await state.set_state(TaskStates.waiting_for_photo)
    else:
        await callback.answer(
            "😢 Вы ещё не подписаны на канал EXEED",
            show_alert=True
        )
        
        await callback.message.edit_text(
            "📢 Пожалуйста, подпишитесь на канал EXEED и нажмите «Готово» 👇",
            reply_markup=get_subscription_keyboard()
        )


@router.message(TaskStates.checking_subscription)
async def handle_waiting_for_subscription(message: Message):
    """Handle messages when waiting for subscription check."""
    await message.answer(
        "📢 Пожалуйста, сначала подпишитесь на канал и нажмите кнопку «Готово» под сообщением выше 👆",
        reply_markup=get_subscription_keyboard()
    )
