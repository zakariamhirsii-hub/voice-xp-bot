import sqlite3
from datetime import datetime, timedelta
from discord.ext import commands, tasks
import os


class DatabaseHandler:
    """Handles all database operations"""

    def __init__(self, db_path="data/xp.db"):
        self.db_path = db_path
        self._init_tables()

    def _get_conn(self):
        """Get database connection"""
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_tables(self):
        """Initialize database tables"""
        with self._get_conn() as conn:
            # Main XP table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS xp_users (
                    user_id TEXT,
                    guild_id TEXT,
                    total_xp INTEGER DEFAULT 0,
                    total_minutes INTEGER DEFAULT 0,
                    daily_xp INTEGER DEFAULT 0,
                    weekly_xp INTEGER DEFAULT 0,
                    monthly_xp INTEGER DEFAULT 0,
                    streak INTEGER DEFAULT 0,
                    last_voice_date TEXT,
                    level INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, guild_id)
                )
            ''')

            # Indexes for faster queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_total_xp ON xp_users(guild_id, total_xp DESC)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_weekly_xp ON xp_users(guild_id, weekly_xp DESC)')

            # XP queue table for batch processing
            conn.execute('''
                CREATE TABLE IF NOT EXISTS xp_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    guild_id TEXT,
                    xp_amount INTEGER,
                    minutes INTEGER,
                    timestamp TEXT
                )
            ''')

    async def get_user(self, user_id: int, guild_id: int) -> dict:
        """Get user data from database"""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT total_xp, total_minutes, daily_xp, weekly_xp,
                       monthly_xp, streak, level
                FROM xp_users
                WHERE user_id = ? AND guild_id = ?
            ''', (str(user_id), str(guild_id)))

            row = cur.fetchone()

            if not row:
                # Create new user
                cur.execute('''
                    INSERT INTO xp_users (user_id, guild_id)
                    VALUES (?, ?)
                ''', (str(user_id), str(guild_id)))
                conn.commit()
                return {
                    "total_xp": 0, "total_minutes": 0,
                    "daily_xp": 0, "weekly_xp": 0,
                    "monthly_xp": 0, "streak": 0, "level": 0
                }

            return dict(row)

    async def add_queue(self, user_id: int, guild_id: int, minutes: int, multiplier: float = 1.0):
        """Add XP to processing queue"""
        xp = int(minutes * 10 * multiplier)

        with self._get_conn() as conn:
            conn.execute('''
                INSERT INTO xp_queue (user_id, guild_id, xp_amount, minutes, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(user_id), str(guild_id), xp, minutes, datetime.now()))

    async def process_queue(self, limit: int = 50):
        """Process queued XP in batches"""
        from cogs.config_cog import config

        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute('SELECT id, user_id, guild_id, xp_amount, minutes FROM xp_queue LIMIT ?', (limit,))
            batch = cur.fetchall()

            for item in batch:
                await self._add_xp(
                    int(item["user_id"]),
                    int(item["guild_id"]),
                    item["xp_amount"],
                    item["minutes"]
                )

            if batch:
                ids = [str(item["id"]) for item in batch]
                conn.execute(f'DELETE FROM xp_queue WHERE id IN ({",".join(ids)})')
                conn.commit()

            return len(batch)

    async def _add_xp(self, user_id: int, guild_id: int, xp_amount: int, minutes: int):
        """Process a single XP addition"""
        from cogs.config_cog import config

        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT daily_xp, total_xp, streak, last_voice_date, level
                FROM xp_users WHERE user_id = ? AND guild_id = ?
            ''', (str(user_id), str(guild_id)))

            row = cur.fetchone()

            if not row:
                return

            daily = row["daily_xp"]
            total = row["total_xp"]
            streak = row["streak"] or 0
            last_voice = row["last_voice_date"]
            old_level = row["level"]

            # Update streak
            today = datetime.now().date()
            if last_voice:
                last_date = datetime.fromisoformat(last_voice).date()
                if last_date == today - timedelta(days=1):
                    streak += 1
                elif last_date < today - timedelta(days=1):
                    streak = 1
            else:
                streak = 1

            # Apply streak multiplier
            mult = 1.0
            for days, m in config.streak_multipliers.items():
                if streak >= days:
                    mult = m

            xp = int(xp_amount * mult)

            # Check daily limit
            if daily + xp > config.max_daily_xp:
                xp = max(0, config.max_daily_xp - daily)

            if xp > 0:
                new_total = total + xp
                new_level = int((new_total / 100) ** 0.5)

                cur.execute('''
                    UPDATE xp_users
                    SET total_xp = ?,
                        total_minutes = total_minutes + ?,
                        daily_xp = ?,
                        weekly_xp = weekly_xp + ?,
                        monthly_xp = monthly_xp + ?,
                        streak = ?,
                        last_voice_date = ?,
                        level = ?
                    WHERE user_id = ? AND guild_id = ?
                ''', (new_total, minutes, daily + xp, xp, xp,
                      streak, datetime.now(), new_level,
                      str(user_id), str(guild_id)))

                conn.commit()

    async def get_leaderboard(self, guild_id: int, stat: str = "total_xp", limit: int = 10) -> list:
        """Get leaderboard data"""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(f'''
                SELECT user_id, {stat}, total_minutes, level
                FROM xp_users
                WHERE guild_id = ?
                ORDER BY {stat} DESC
                LIMIT ?
            ''', (str(guild_id), limit))
            return cur.fetchall()


# Database singleton
_db = DatabaseHandler()


class DatabaseCog(commands.Cog):
    """Database management cog"""

    def __init__(self, bot):
        self.bot = bot
        self.db = _db
        self.processing.start()

    @tasks.loop(seconds=10)
    async def processing(self):
        """Process XP queue every 10 seconds"""
        try:
            processed = await self.db.process_queue()
            if processed > 0:
                print(f"📊 Processed {processed} XP items")
        except Exception as e:
            print(f"❌ Queue processing error: {e}")

    @processing.before_loop
    async def before_processing(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(DatabaseCog(bot))