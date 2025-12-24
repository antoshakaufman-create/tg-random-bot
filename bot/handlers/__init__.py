from aiogram import Router

from bot.handlers.start import router as start_router
from bot.handlers.subscription import router as subscription_router
from bot.handlers.tasks import router as tasks_router
from bot.handlers.result import router as result_router


def setup_routers() -> Router:
    """Setup and return main router with all handlers."""
    main_router = Router()
    
    main_router.include_router(start_router)
    main_router.include_router(subscription_router)
    main_router.include_router(tasks_router)
    main_router.include_router(result_router)
    
    return main_router
