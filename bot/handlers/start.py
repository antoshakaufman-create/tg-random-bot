from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.handlers.states import RegistrationStates, TaskStates
from bot.keyboards import get_phone_keyboard, get_subscription_keyboard
from bot.database import get_or_create_participant, update_participant

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command."""
    # Clear any previous state
    await state.clear()
    
    # Get or create participant
    user = message.from_user
    await get_or_create_participant(user.id, user.username)
    
    await message.answer(
        "👋 Привет! Как вас зовут?"
    )
    
    await state.set_state(RegistrationStates.waiting_for_name)


@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Process user's name."""
    if not message.text:
        await message.answer("❤️ Пожалуйста, введите ваше имя (не менее 2 букв).")
        return

    name = message.text.strip()
    
    if len(name) < 2 or len(name) > 100:
        await message.answer("❤️ Пожалуйста, введите ваше имя (не менее 2 букв).")
        return
    
    # Save name to database
    await update_participant(message.from_user.id, name=name)
    
    await message.answer(
        f"✨ Приятно познакомиться, <b>{name}</b>!\n\n"
        "📱 Теперь укажите ваш номер телефона.\n"
        "Нажмите кнопку ниже или введите вручную 👇",
        parse_mode="HTML",
        reply_markup=get_phone_keyboard()
    )
    
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Process shared contact."""
    phone = message.contact.phone_number
    
    # Save phone to database
    await update_participant(message.from_user.id, phone=phone)
    
    await message.answer(
        "✅ Отлично, номер сохранён!\n\n"
        "📢 Подпишитесь на наши каналы и нажмите «Готово» 👇",
        reply_markup=ReplyKeyboardRemove()
    )
    
    await message.answer(
        "👇 Выберите канал для подписки:",
        reply_markup=get_subscription_keyboard()
    )
    
    await state.set_state(TaskStates.checking_subscription)


@router.message(RegistrationStates.waiting_for_phone)
async def process_phone_text(message: Message, state: FSMContext):
    """Handle text input when expecting phone."""
    # Check if message has text
    if not message.text:
        await message.answer(
            "🙏 Пожалуйста, введите номер телефона или нажмите кнопку ниже 👇",
            reply_markup=get_phone_keyboard()
        )
        return
    
    text = message.text.strip()
    
    # Simple phone validation (allows various formats)
    digits = ''.join(filter(str.isdigit, text))

    
    if len(digits) >= 10 and len(digits) <= 15:
        # Save phone to database
        await update_participant(message.from_user.id, phone=text)
        
        await message.answer(
            "✅ Отлично, номер сохранён!\n\n"
            "📢 Подпишитесь на наши каналы и нажмите «Готово» 👇",
            reply_markup=ReplyKeyboardRemove()
        )
        
        await message.answer(
            "👇 Выберите канал для подписки:",
            reply_markup=get_subscription_keyboard()
        )
        
        await state.set_state(TaskStates.checking_subscription)
    else:
        await message.answer(
            "🙏 Пожалуйста, введите корректный номер телефона или нажмите кнопку 👇",
            reply_markup=get_phone_keyboard()
        )
