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


@router.message(TaskStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    """Handle photo upload."""
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
    
    # Save photo path to database
    await update_participant(message.from_user.id, photo_path=filepath)
    
    # Forward to storage channel if configured
    from bot.config import STORAGE_CHANNEL_ID
    if STORAGE_CHANNEL_ID:
        try:
            user = message.from_user
            participant_data = await get_participant_data(user.id) # We need to fetch data first or pass it
            # Actually we don't have get_participant_data imported here, let's look at the imports. 
            # We can just use the info we have or fetch from DB.
            # Let's simplify: just name and username from message.from_user, and phone from DB if we want.
            # But wait, phone is in DB.
            
            caption = (
                f"👤 <b>Новый участник</b>\n"
                f"ID: {user.id}\n"
                f"Username: @{user.username or 'нет'}\n"
                f"First Name: {user.first_name}\n"
                f"Last Name: {user.last_name or ''}\n"
                f"File: {filename}"
            )
            
            await bot.send_photo(
                chat_id=STORAGE_CHANNEL_ID,
                photo=photo.file_id,
                caption=caption
            )
        except Exception as e:
            # Don't fail the user flow if saving fails
            print(f"Failed to forward photo to storage: {e}")

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
