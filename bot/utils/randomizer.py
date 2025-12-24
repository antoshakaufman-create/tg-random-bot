"""
Smart prize randomizer with time-based distribution.
Ensures prizes are distributed evenly across operating hours.
Uses Moscow timezone (UTC+3) since the rink is in Moscow.
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

# Operating hours configuration (Moscow time)
OPEN_TIME = time(9, 30)   # 9:30
CLOSE_TIME = time(22, 30)  # 22:30


def get_moscow_time() -> datetime:
    """Get current time in Moscow timezone."""
    return datetime.now(MOSCOW_TZ)


def get_day_progress() -> float:
    """
    Calculate progress through the operating day (0.0 to 1.0).
    Uses Moscow timezone.
    
    Returns:
        float: 0.0 at opening, 1.0 at closing, clamped to [0, 1]
    """
    now = get_moscow_time().time()
    
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
    
    Uses PURE TIME-BASED distribution:
    - Prizes are distributed evenly across operating hours
    - Works with ANY number of participants
    - If behind schedule → higher probability
    - If ahead of schedule → lower probability
    
    Returns:
        tuple: (is_winner, prize_name or None, prize_type: 'big'/'small'/None)
    """
    stats = await get_daily_stats()
    small_given = stats.get("small_prizes_given", 0)
    big_given = stats.get("big_prizes_given", 0)
    
    remaining_big = DAILY_BIG_PRIZES - big_given
    remaining_small = DAILY_SMALL_PRIZES - small_given
    
    # Get time progress through the day (Moscow time)
    time_progress = get_day_progress()
    
    # Calculate expected prizes by now (based on time only)
    expected_small_by_now = DAILY_SMALL_PRIZES * time_progress
    expected_big_by_now = DAILY_BIG_PRIZES * time_progress
    
    # Calculate deficit (positive = behind, negative = ahead)
    small_deficit = expected_small_by_now - small_given
    big_deficit = expected_big_by_now - big_given
    
    # Remaining time fraction
    remaining_time = max(0.01, 1.0 - time_progress)  # Avoid division by zero
    
    # --- Big Prize Check ---
    if remaining_big > 0:
        # Base: how many prizes should we give in remaining time?
        # If we have 5 prizes left and 50% time left, that's 10 per remaining time
        base_probability = remaining_big / (remaining_time * 100)  # Spread over ~100 participants per hour
        
        # Boost if behind schedule
        if big_deficit > 0:
            boost = 1.0 + (big_deficit * 0.5)  # +50% per prize behind
        else:
            boost = max(0.5, 1.0 + (big_deficit * 0.3))  # Reduce if ahead
        
        big_chance = base_probability * boost
        
        # Cap at 15%
        big_chance = min(big_chance, 0.15)
        
        if random.random() < big_chance:
            prize = random.choice(BIG_PRIZE_LIST)
            return True, prize, "big"
    
    # --- Small Prize Check ---
    if remaining_small > 0:
        base_probability = remaining_small / (remaining_time * 100)
        
        if small_deficit > 0:
            boost = 1.0 + (small_deficit * 0.02)  # +2% per prize behind
        else:
            boost = max(0.5, 1.0 + (small_deficit * 0.01))
        
        small_chance = base_probability * boost
        
        # Cap at 50%
        small_chance = min(small_chance, 0.50)
        
        if random.random() < small_chance:
            prize = random.choice(SMALL_PRIZE_LIST)
            return True, prize, "small"
    
    return False, None, None
