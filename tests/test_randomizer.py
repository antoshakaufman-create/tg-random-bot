"""
Test the randomizer with different participant counts.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock database stats
mock_stats = {
    "small_prizes_given": 0,
    "big_prizes_given": 0,
    "participants_count": 0
}

async def mock_get_daily_stats():
    return mock_stats

# Patch the module
import bot.utils.randomizer as randomizer
randomizer.get_daily_stats = mock_get_daily_stats

from bot.utils.randomizer import check_win, get_day_progress, get_moscow_time


async def test_with_participants(count: int):
    """Test randomizer with specified number of participants."""
    global mock_stats
    mock_stats = {"small_prizes_given": 0, "big_prizes_given": 0, "participants_count": 0}
    
    small_wins = 0
    big_wins = 0
    
    for i in range(count):
        is_winner, prize, prize_type = await check_win()
        
        if prize_type == "big":
            big_wins += 1
            mock_stats["big_prizes_given"] += 1
        elif prize_type == "small":
            small_wins += 1
            mock_stats["small_prizes_given"] += 1
        
        mock_stats["participants_count"] += 1
    
    print(f"\n👥 {count} participants:")
    print(f"   🎁 Small: {small_wins}/100  |  🎉 Big: {big_wins}/5  |  Win rate: {(small_wins + big_wins) / count:.1%}")
    
    return small_wins, big_wins


async def main():
    moscow_time = get_moscow_time()
    progress = get_day_progress()
    
    print("🎲 RANDOMIZER TEST - Flexible Participant Count")
    print("="*60)
    print(f"🕐 Moscow time: {moscow_time.strftime('%H:%M')}")
    print(f"⏰ Day progress: {progress:.1%}")
    
    # Test with various participant counts
    for count in [200, 500, 1000, 2000]:
        await test_with_participants(count)
    
    print("\n" + "="*60)
    print("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
