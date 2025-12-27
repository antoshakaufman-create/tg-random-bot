"""
Event-mode prize randomizer.
Only keychains - EVERYONE WINS!
"""
import random
from bot.config import SMALL_PRIZE_LIST


async def check_win() -> tuple[bool, str | None, str | None]:
    """
    EVERYONE WINS A KEYCHAIN!
    No big prizes left.
    
    Returns:
        tuple: (True, prize_name, "small")
    """
    prize = random.choice(SMALL_PRIZE_LIST)
    return True, prize, "small"
