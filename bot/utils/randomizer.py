import random
from bot.config import (
    DAILY_SMALL_PRIZES, 
    DAILY_BIG_PRIZES, 
    DAILY_VISITORS, 
    SMALL_PRIZE_LIST, 
    BIG_PRIZE_LIST
)
from bot.database import get_daily_stats


async def check_win() -> tuple[bool, str | None, str | None]:
    """
    Check if current participant wins a prize.
    
    Returns:
        tuple: (is_winner, prize_name or None, prize_type: 'big'/'small'/None)
    
    Algorithm:
    - Total prizes = 100 small + 5 big = 105 per day
    - ~6000 visitors per day
    - Big prize chance: 5/6000 = 0.08%
    - Small prize chance: 100/6000 = 1.67%
    """
    stats = await get_daily_stats()
    small_given = stats.get("small_prizes_given", 0)
    big_given = stats.get("big_prizes_given", 0)
    
    remaining_big = DAILY_BIG_PRIZES - big_given
    remaining_small = DAILY_SMALL_PRIZES - small_given
    
    # First check for big prize (lower probability)
    if remaining_big > 0:
        big_chance = remaining_big / DAILY_VISITORS
        if random.random() < big_chance:
            prize = random.choice(BIG_PRIZE_LIST)
            return True, prize, "big"
    
    # Then check for small prize
    if remaining_small > 0:
        small_chance = remaining_small / DAILY_VISITORS
        if random.random() < small_chance:
            prize = random.choice(SMALL_PRIZE_LIST)
            return True, prize, "small"
    
    return False, None, None
