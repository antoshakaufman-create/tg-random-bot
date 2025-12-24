import os
from datetime import datetime
from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.handlers.states import TaskStates
from bot.keyboards import get_finish_keyboard
from bot.database import update_participant
from bot.config import PHOTOS_DIR

router = Router()


import logging

logger = logging.getLogger(__name__)

@router.message(TaskStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    """Handle photo upload."""
    logger.info(f"Photo received from user {message.from_user.id}")
    # Get the largest photo (best quality)
    photo = message.photo[-1]
    
    # Create filename with user_id and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{message.from_user.id}_{timestamp}.jpg"
    filepath = os.path.join(PHOTOS_DIR, filename)
    
    # Ensure photos directory exists
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    
    # Download and save photo
    file = await bot.get_file(photo.file_id)
    await bot.download_file(file.file_path, filepath)
    
    # Get participant data (name, phone)
    from bot.database import get_or_create_participant, get_next_participant_number
    participant = await get_or_create_participant(message.from_user.id)
    
    # Generate participant number immediately
    participant_number = await get_next_participant_number()
    
    # Save photo path and number to database
    await update_participant(
        message.from_user.id, 
        photo_path=filepath,
        participant_number=participant_number
    )
    
    # Forward to storage channel if configured
    from bot.config import STORAGE_CHANNEL_ID
    logger.info(f"DEBUG: STORAGE_CHANNEL_ID value is '{STORAGE_CHANNEL_ID}'")
    
    if STORAGE_CHANNEL_ID:
        try:
            user = message.from_user
            name = participant.get("name", "Не указано")
            phone = participant.get("phone", "Не указано")
            username = f"@{user.username}" if user.username else "Нет"
            
            caption = (
                f"👤 <b>Новый участник #{participant_number}</b>\n\n"
                f"🆔 ID: <code>{user.id}</code>\n"
                f"👤 Имя: {name}\n"
                f"📱 Телефон: {phone}\n"
                f"🔗 Username: {username}\n\n"
                f"📁 Файл: {filename}"
            )
            
            await bot.send_photo(
                chat_id=STORAGE_CHANNEL_ID,
                photo=photo.file_id,
                caption=caption
            )
        except Exception as e:
            # Debugging: Show error to user
            logger.error(f"Failed to forward photo: {e}")
            await message.answer(f"⚠️ <b>Debug:</b> Не удалось переслать фото в канал.\nОшибка: {str(e)}", parse_mode="HTML")

    await message.answer(
        "📸 <b>Отлично! Фото сохранено!</b>\n\n"
        "🎟 Нажмите кнопку ниже, чтобы получить номер участника и узнать, выиграли ли вы приз!",
        parse_mode="HTML",
        reply_markup=get_finish_keyboard()
    )
    
    await state.set_state(TaskStates.ready_for_result)


@router.message(TaskStates.waiting_for_photo)
async def handle_no_photo(message: Message, state: FSMContext):
    """Handle non-photo messages when expecting photo."""
    await message.answer(
        "❌ Пожалуйста, отправьте фото.\n\n"
        "Сделайте классное фото на катке и отправьте его сюда! 📷"
    )
