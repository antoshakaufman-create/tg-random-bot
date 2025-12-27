"""
Event-mode prize randomizer.
Configured for: 100 participants, 95 small prizes, 5 big prizes in 3 hours.
Everyone wins! 5% chance of big prize, 95% chance of small prize.
"""
import random
from datetime import datetime, time, timezone, timedelta
from bot.config import (
    DAILY_SMALL_PRIZES, 
    DAILY_BIG_PRIZES, 
    SMALL_PRIZE_LIST, 
    BIG_PRIZE_LIST
)
from bot.database import get_daily_stats


# Moscow timezone (UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))


def get_moscow_time() -> datetime:
    """Get current time in Moscow timezone."""
    return datetime.now(MOSCOW_TZ)


async def check_win() -> tuple[bool, str | None, str | None]:
    """
    EVENT MODE: Everyone wins!
    - 5% chance of BIG prize (подарочный набор)
    - 95% chance of SMALL prize (брелок)
    
    Returns:
        tuple: (is_winner, prize_name or None, prize_type: 'big'/'small'/None)
    """
    stats = await get_daily_stats()
    small_given = stats.get("small_prizes_given", 0)
    big_given = stats.get("big_prizes_given", 0)
    
    remaining_big = DAILY_BIG_PRIZES - big_given
    remaining_small = DAILY_SMALL_PRIZES - small_given
    
    # If no prizes left, no win
    if remaining_big <= 0 and remaining_small <= 0:
        return False, None, None
    
    # Big prize check: 5% base chance, but only if available
    if remaining_big > 0:
        big_chance = 0.05  # 5% for big prize
        
        # Increase chance if running low and need to give them out
        if remaining_big > 0 and remaining_small == 0:
            big_chance = 1.0  # Only big prizes left
        
        if random.random() < big_chance:
            prize = random.choice(BIG_PRIZE_LIST)
            return True, prize, "big"
    
    # Small prize: everyone else wins small
    if remaining_small > 0:
        prize = random.choice(SMALL_PRIZE_LIST)
        return True, prize, "small"
    
    # Fallback: no prizes available
    return False, None, None
