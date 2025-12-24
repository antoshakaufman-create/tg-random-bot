"""
Stress test for the bot's database operations.
Simulates high concurrency to measure performance.
"""
import asyncio
import time
import random
import string
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database import init_db, get_or_create_participant, update_participant, get_next_participant_number
from bot.config import DATABASE_PATH


async def simulate_user(user_id: int) -> dict:
    """Simulate a single user going through the full flow."""
    start = time.perf_counter()
    
    # Step 1: Create participant
    await get_or_create_participant(user_id, f"user_{user_id}")
    
    # Step 2: Update name
    name = ''.join(random.choices(string.ascii_letters, k=10))
    await update_participant(user_id, name=name)
    
    # Step 3: Update phone
    phone = f"+7{random.randint(9000000000, 9999999999)}"
    await update_participant(user_id, phone=phone)
    
    # Step 4: Update photo path
    photo_path = f"/photos/{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    await update_participant(user_id, photo_path=photo_path)
    
    # Step 5: Get participant number
    number = await get_next_participant_number()
    await update_participant(user_id, participant_number=number)
    
    # Step 6: Update prize status
    is_winner = random.choice([True, False])
    prize = "Брелок" if is_winner else None
    await update_participant(user_id, is_winner=is_winner, prize=prize)
    
    elapsed = time.perf_counter() - start
    return {"user_id": user_id, "time": elapsed}


async def run_stress_test(num_users: int, concurrency: int):
    """Run stress test with specified number of users and concurrency."""
    print(f"\n{'='*60}")
    print(f"🚀 STRESS TEST: {num_users} users, {concurrency} concurrent")
    print(f"{'='*60}")
    
    # Initialize DB
    await init_db()
    
    # Remove old test DB if exists
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    await init_db()
    
    start_time = time.perf_counter()
    
    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(concurrency)
    
    async def limited_task(user_id):
        async with semaphore:
            return await simulate_user(user_id)
    
    # Run all users
    tasks = [limited_task(i) for i in range(1, num_users + 1)]
    results = await asyncio.gather(*tasks)
    
    total_time = time.perf_counter() - start_time
    
    # Calculate stats
    times = [r["time"] for r in results]
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    
    print(f"\n📊 RESULTS:")
    print(f"   Total time:     {total_time:.2f}s")
    print(f"   Users/second:   {num_users / total_time:.1f}")
    print(f"   Avg per user:   {avg_time * 1000:.1f}ms")
    print(f"   Min per user:   {min_time * 1000:.1f}ms")
    print(f"   Max per user:   {max_time * 1000:.1f}ms")
    
    # Extrapolate
    users_per_hour = (num_users / total_time) * 3600
    print(f"\n📈 CAPACITY ESTIMATE:")
    print(f"   Users per hour: {users_per_hour:,.0f}")
    print(f"   Users per day:  {users_per_hour * 24:,.0f}")
    
    return {
        "total_time": total_time,
        "users_per_second": num_users / total_time,
        "avg_time_ms": avg_time * 1000
    }


async def main():
    print("🧪 Bot Database Stress Test")
    print("="*60)
    
    # Test 1: Low load (normal day)
    await run_stress_test(num_users=100, concurrency=10)
    
    # Test 2: Medium load (busy hour)
    await run_stress_test(num_users=500, concurrency=50)
    
    # Test 3: High load (peak)
    await run_stress_test(num_users=1000, concurrency=100)
    
    print("\n" + "="*60)
    print("✅ Stress test completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
