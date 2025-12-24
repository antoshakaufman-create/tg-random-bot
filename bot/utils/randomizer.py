"""
Smart prize randomizer with time-based distribution.
Ensures prizes are distributed evenly across operating hours.
"""
import random
from datetime import datetime, time
from bot.config import (
    DAILY_SMALL_PRIZES, 
    DAILY_BIG_PRIZES, 
    DAILY_VISITORS, 
    SMALL_PRIZE_LIST, 
    BIG_PRIZE_LIST
)
from bot.database import get_daily_stats


# Operating hours configuration
OPEN_TIME = time(9, 30)   # 9:30
CLOSE_TIME = time(22, 30)  # 22:30


def get_day_progress() -> float:
    """
    Calculate progress through the operating day (0.0 to 1.0).
    
    Returns:
        float: 0.0 at opening, 1.0 at closing, clamped to [0, 1]
    """
    now = datetime.now().time()
    
    # Convert times to minutes since midnight
    now_minutes = now.hour * 60 + now.minute
    open_minutes = OPEN_TIME.hour * 60 + OPEN_TIME.minute
    close_minutes = CLOSE_TIME.hour * 60 + CLOSE_TIME.minute
    
    # Calculate progress
    total_minutes = close_minutes - open_minutes  # 780 minutes = 13 hours
    elapsed = now_minutes - open_minutes
    
    progress = elapsed / total_minutes
    
    # Clamp to [0, 1]
    return max(0.0, min(1.0, progress))


async def check_win() -> tuple[bool, str | None, str | None]:
    """
    Check if current participant wins a prize.
    
    Uses time-based distribution to ensure prizes are given out
    evenly throughout operating hours.
    
    Returns:
        tuple: (is_winner, prize_name or None, prize_type: 'big'/'small'/None)
    """
    stats = await get_daily_stats()
    small_given = stats.get("small_prizes_given", 0)
    big_given = stats.get("big_prizes_given", 0)
    participants_count = stats.get("participants_count", 0)
    
    remaining_big = DAILY_BIG_PRIZES - big_given
    remaining_small = DAILY_SMALL_PRIZES - small_given
    
    # Get time progress through the day
    time_progress = get_day_progress()
    
    # Calculate expected prizes by now
    expected_small_by_now = DAILY_SMALL_PRIZES * time_progress
    expected_big_by_now = DAILY_BIG_PRIZES * time_progress
    
    # Calculate how far behind/ahead we are
    small_deficit = expected_small_by_now - small_given
    big_deficit = expected_big_by_now - big_given
    
    # Remaining participants estimate (based on time or actual count)
    remaining_time = 1.0 - time_progress
    estimated_remaining = max(1, DAILY_VISITORS * remaining_time)
    
    # --- Big Prize Check ---
    if remaining_big > 0:
        # Base probability
        base_chance = remaining_big / estimated_remaining
        
        # Adjust based on deficit (if behind, increase; if ahead, decrease)
        if big_deficit > 0:
            # Behind schedule - boost probability
            adjustment = 1.0 + (big_deficit / DAILY_BIG_PRIZES)
        else:
            # Ahead of schedule - reduce probability
            adjustment = max(0.3, 1.0 + (big_deficit / DAILY_BIG_PRIZES))
        
        big_chance = base_chance * adjustment
        
        # Cap at 15% to avoid giving too many at once
        big_chance = min(big_chance, 0.15)
        
        if random.random() < big_chance:
            prize = random.choice(BIG_PRIZE_LIST)
            return True, prize, "big"
    
    # --- Small Prize Check ---
    if remaining_small > 0:
        base_chance = remaining_small / estimated_remaining
        
        if small_deficit > 0:
            adjustment = 1.0 + (small_deficit / DAILY_SMALL_PRIZES)
        else:
            adjustment = max(0.3, 1.0 + (small_deficit / DAILY_SMALL_PRIZES))
        
        small_chance = base_chance * adjustment
        
        # Cap at 40% to maintain excitement
        small_chance = min(small_chance, 0.40)
        
        if random.random() < small_chance:
            prize = random.choice(SMALL_PRIZE_LIST)
            return True, prize, "small"
    
    return False, None, None
