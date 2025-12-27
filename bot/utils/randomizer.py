"""
Event-mode prize randomizer.
- UNLIMITED keychains (everyone wins at least a keychain)
- Only 5 gift sets available (5% chance while available)
"""
import random
from datetime import datetime, timezone, timedelta
from bot.config import (
    DAILY_BIG_PRIZES, 
    BIG_PRIZE_LIST,
    SMALL_PRIZE_LIST
)
from bot.database import get_daily_stats


# Moscow timezone (UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))


def get_moscow_time() -> datetime:
    """Get current time in Moscow timezone."""
    return datetime.now(MOSCOW_TZ)


async def check_win() -> tuple[bool, str | None, str | None]:
    """
    EVENT MODE: EVERYONE WINS!
    - 5% chance of BIG prize (подарочный набор) if still available
    - 100% chance of SMALL prize (брелок) - UNLIMITED
    
    Returns:
        tuple: (is_winner, prize_name, prize_type: 'big'/'small')
    """
    stats = await get_daily_stats()
    big_given = stats.get("big_prizes_given", 0)
    remaining_big = DAILY_BIG_PRIZES - big_given
    
    # Big prize check: 5% chance if available
    if remaining_big > 0:
        if random.random() < 0.05:  # 5% for big prize
            prize = random.choice(BIG_PRIZE_LIST)
            return True, prize, "big"
    
    # Everyone else wins a keychain (UNLIMITED)
    prize = random.choice(SMALL_PRIZE_LIST)
    return True, prize, "small"
