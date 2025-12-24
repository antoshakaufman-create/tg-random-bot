import aiosqlite
from datetime import date
from bot.config import DATABASE_PATH


async def init_db():
    """Initialize database tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                name TEXT,
                phone TEXT,
                photo_path TEXT,
                participant_number INTEGER,
                is_winner BOOLEAN DEFAULT 0,
                prize TEXT,
                prize_type TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                participants_count INTEGER DEFAULT 0,
                small_prizes_given INTEGER DEFAULT 0,
                big_prizes_given INTEGER DEFAULT 0
            )
        """)
        
        await db.commit()


async def get_or_create_participant(telegram_id: int, username: str = None) -> dict:
    """Get existing participant or create new one."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM participants WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            return dict(row)
        
        # Create new participant
        await db.execute(
            "INSERT INTO participants (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username)
        )
        await db.commit()
        
        cursor = await db.execute(
            "SELECT * FROM participants WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        return dict(row)


async def update_participant(telegram_id: int, **kwargs) -> None:
    """Update participant fields."""
    if not kwargs:
        return
    
    fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [telegram_id]
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            f"UPDATE participants SET {fields} WHERE telegram_id = ?",
            values
        )
        await db.commit()


async def get_next_participant_number() -> int:
    """Get next sequential participant number."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT COALESCE(MAX(participant_number), 0) + 1 FROM participants"
        )
        row = await cursor.fetchone()
        return row[0]


async def get_daily_stats(target_date: date = None) -> dict:
    """Get daily statistics."""
    if target_date is None:
        target_date = date.today()
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM daily_stats WHERE date = ?",
            (target_date.isoformat(),)
        )
        row = await cursor.fetchone()
        
        if row:
            return dict(row)
        
        # Create new daily stats
        await db.execute(
            "INSERT INTO daily_stats (date, participants_count, small_prizes_given, big_prizes_given) VALUES (?, 0, 0, 0)",
            (target_date.isoformat(),)
        )
        await db.commit()
        
        return {
            "date": target_date.isoformat(),
            "participants_count": 0,
            "small_prizes_given": 0,
            "big_prizes_given": 0
        }


async def increment_daily_stats(small_prizes: int = 0, big_prizes: int = 0, participants: int = 0) -> None:
    """Increment daily statistics."""
    today = date.today().isoformat()
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Ensure row exists
        await db.execute(
            "INSERT OR IGNORE INTO daily_stats (date, participants_count, small_prizes_given, big_prizes_given) VALUES (?, 0, 0, 0)",
            (today,)
        )
        
        await db.execute(
            """UPDATE daily_stats 
               SET participants_count = participants_count + ?,
                   small_prizes_given = small_prizes_given + ?,
                   big_prizes_given = big_prizes_given + ?
               WHERE date = ?""",
            (participants, small_prizes, big_prizes, today)
        )
        await db.commit()
