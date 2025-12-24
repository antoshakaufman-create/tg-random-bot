from aiogram import Router, Bot
from aiogram.types import CallbackQuery
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
    
    # Check both channels
    exeed_subscribed = await check_user_subscription(bot, user_id, EXEED_CHANNEL_ID)
    luzhniki_subscribed = await check_user_subscription(bot, user_id, LUZHNIKI_CHANNEL_ID)
    
    if exeed_subscribed and luzhniki_subscribed:
        # User is subscribed to both channels
        await callback.message.edit_text(
            "✅ <b>Отлично! Вы подписаны на оба канала!</b>\n\n"
            "📸 <b>Шаг 4:</b> Сделайте фото на катке и отправьте его в этот чат.\n\n"
            "Просто сделайте классное фото и отправьте его сюда! 📷",
            parse_mode="HTML"
        )
        
        await state.set_state(TaskStates.waiting_for_photo)
    else:
        # User not subscribed to one or both channels
        not_subscribed = []
        if not exeed_subscribed:
            not_subscribed.append("EXEED Russia")
        if not luzhniki_subscribed:
            not_subscribed.append("Лужники")
        
        channels_text = " и ".join(not_subscribed)
        
        await callback.answer(
            f"❌ Вы не подписаны на: {channels_text}",
            show_alert=True
        )
        
        await callback.message.edit_text(
            f"❌ <b>Вы ещё не подписаны на: {channels_text}</b>\n\n"
            "Пожалуйста, подпишитесь на каналы и нажмите кнопку снова:",
            parse_mode="HTML",
            reply_markup=get_subscription_keyboard()
        )
