"""
Smart prize randomizer with time-based distribution.
Ensures prizes are distributed evenly across operating hours.
Uses Moscow timezone (UTC+3) since the rink is in Moscow.

Distribution schedule:
- 9:30-12:00 (morning): Low probability - save prizes
- 12:00-17:00 (afternoon): Normal probability
- 17:00-22:30 (evening): Higher probability - ensure all given
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
    """
    now = get_moscow_time().time()
    
    now_minutes = now.hour * 60 + now.minute
    open_minutes = OPEN_TIME.hour * 60 + OPEN_TIME.minute
    close_minutes = CLOSE_TIME.hour * 60 + CLOSE_TIME.minute
    
    total_minutes = close_minutes - open_minutes  # 780 minutes = 13 hours
    elapsed = now_minutes - open_minutes
    
    progress = elapsed / total_minutes
    return max(0.0, min(1.0, progress))


def get_time_weight() -> float:
    """
    Get probability weight based on time of day.
    Returns multiplier (0.5 to 2.0) for prize probability.
    
    Schedule:
    - 9:30-11:30 (first 2 hours): 0.5x - save prizes for later
    - 11:30-17:00 (middle): 1.0x - normal distribution
    - 17:00-20:30 (evening): 1.3x - slightly higher
    - 20:30-22:30 (last 2 hours): 2.0x - give remaining prizes
    """
    progress = get_day_progress()
    
    if progress < 0.15:  # First 2 hours (9:30-11:30)
        return 0.5
    elif progress < 0.58:  # 11:30-17:00
        return 1.0
    elif progress < 0.85:  # 17:00-20:30
        return 1.3
    else:  # Last 2 hours (20:30-22:30)
        return 2.0


async def check_win() -> tuple[bool, str | None, str | None]:
    """
    Check if current participant wins a prize.
    
    Uses time-weighted distribution:
    - Morning: Lower probability (save prizes)
    - Evening: Higher probability (ensure all distributed)
    - End of day: Very high probability (must give remaining)
    
    Returns:
        tuple: (is_winner, prize_name or None, prize_type: 'big'/'small'/None)
    """
    stats = await get_daily_stats()
    small_given = stats.get("small_prizes_given", 0)
    big_given = stats.get("big_prizes_given", 0)
    
    remaining_big = DAILY_BIG_PRIZES - big_given
    remaining_small = DAILY_SMALL_PRIZES - small_given
    
    # Time-based calculations
    time_progress = get_day_progress()
    time_weight = get_time_weight()
    remaining_time = max(0.01, 1.0 - time_progress)
    
    # Expected prizes by now
    expected_small = DAILY_SMALL_PRIZES * time_progress
    expected_big = DAILY_BIG_PRIZES * time_progress
    
    # Deficit (positive = behind schedule)
    small_deficit = expected_small - small_given
    big_deficit = expected_big - big_given
    
    # --- Big Prize Check ---
    if remaining_big > 0:
        # Base probability: spread remaining over remaining time
        base_prob = (remaining_big / DAILY_BIG_PRIZES) * 0.02  # ~2% base
        
        # Adjust for deficit
        if big_deficit > 0:
            deficit_mult = 1.0 + (big_deficit * 0.5)
        else:
            deficit_mult = max(0.3, 1.0 + (big_deficit * 0.2))
        
        # Force distribution near end of day
        if time_progress > 0.9:  # Last 10% of day
            urgency = 1.0 + (remaining_big * 0.5)  # +50% per remaining prize
        else:
            urgency = 1.0
        
        big_chance = base_prob * time_weight * deficit_mult * urgency
        big_chance = min(big_chance, 0.20)  # Cap at 20%
        
        if random.random() < big_chance:
            prize = random.choice(BIG_PRIZE_LIST)
            return True, prize, "big"
    
    # --- Small Prize Check ---
    if remaining_small > 0:
        base_prob = (remaining_small / DAILY_SMALL_PRIZES) * 0.25  # ~25% base
        
        if small_deficit > 0:
            deficit_mult = 1.0 + (small_deficit * 0.02)
        else:
            deficit_mult = max(0.3, 1.0 + (small_deficit * 0.01))
        
        if time_progress > 0.9:
            urgency = 1.0 + (remaining_small * 0.02)
        else:
            urgency = 1.0
        
        small_chance = base_prob * time_weight * deficit_mult * urgency
        small_chance = min(small_chance, 0.60)  # Cap at 60%
        
        if random.random() < small_chance:
            prize = random.choice(SMALL_PRIZE_LIST)
            return True, prize, "small"
    
    return False, None, None
