from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from bot.config import EXEED_CHANNEL_URL, LUZHNIKI_CHANNEL_URL


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with share contact button."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поделиться номером телефона", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Keyboard with channel links and check button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 EXEED Russia", url=EXEED_CHANNEL_URL)],
            [InlineKeyboardButton(text="🏟 Лужники", url=LUZHNIKI_CHANNEL_URL)],
            [InlineKeyboardButton(text="✅ Готово", callback_data="check_subscription")]
        ]
    )


def get_finish_keyboard() -> InlineKeyboardMarkup:
    """Keyboard to get participant number."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎟 Получить номер участника", callback_data="get_result")]
        ]
    )
