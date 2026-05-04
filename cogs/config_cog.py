import discord
from discord.ext import commands
from dataclasses import dataclass
from typing import Dict


@dataclass
class BotConfig:
    """Central configuration for the XP system"""

    # XP Rates
    xp_per_minute: int = 10
    max_daily_xp: int = 500

    # Streak multipliers (days -> multiplier)
    streak_multipliers: Dict[int, float] = None

    # Channel multipliers (keyword -> multiplier)
    channel_multipliers: Dict[str, float] = None

    # Time multipliers (start, end, multiplier)
    time_multipliers: Dict[str, tuple] = None

    # AFK Settings
    afk_channel_names: list = None
    allow_muted: bool = False
    allow_deafened: bool = False
    allow_alone: bool = False

    def __post_init__(self):
        # Streak bonuses
        self.streak_multipliers = {
            3: 1.25,
            5: 1.5,
            7: 2.0,
            14: 2.5,
            30: 3.0
        }

        # Channel type multipliers
        self.channel_multipliers = {
            "gaming": 1.3, "game": 1.3,
            "study": 0.7, "homework": 0.7,
            "music": 1.2, "karaoke": 1.5,
            "meeting": 0.5, "work": 0.5,
            "chill": 1.0, "relax": 1.0
        }

        # Time bonuses
        self.time_multipliers = {
            "morning": (6, 12, 1.2),
            "night": (22, 2, 1.25),
            "weekend": (5, 6, 1.5)
        }

        # AFK channel names
        self.afk_channel_names = ["afk", "idle", "sleep", "away"]


# Global config instance
config = BotConfig()


class ConfigCog(commands.Cog):
    """Configuration management cog"""

    def __init__(self, bot):
        self.bot = bot
        self.bot.xp_config = config


async def setup(bot):
    await bot.add_cog(ConfigCog(bot))