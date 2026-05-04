import discord
from discord.ext import commands
from datetime import datetime


class UserCommandsCog(commands.Cog):
    """User-facing commands for the XP system"""

    def __init__(self, bot):
        self.bot = bot

    def format_time(self, minutes: int) -> str:
        """Format minutes into readable time"""
        hours = minutes // 60
        days = hours // 24

        if days > 0:
            return f"{days}d {hours % 24}h"
        elif hours > 0:
            return f"{hours}h {minutes % 60}m"
        else:
            return f"{minutes}m"

    @commands.hybrid_command(name="voice", description="View your voice XP stats")
    async def voice_stats(self, ctx, member: discord.Member = None):
        """Display voice XP statistics for a user"""
        target = member or ctx.author

        from cogs.database_cog import _db
        data = await _db.get_user(target.id, ctx.guild.id)

        level = data["level"]
        next_level_xp = ((level + 1) ** 2) * 100
        xp_needed = next_level_xp - data["total_xp"]

        # Progress bar
        current_level_xp = (level ** 2) * 100
        xp_in_level = data["total_xp"] - current_level_xp
        level_up_needed = next_level_xp - current_level_xp
        progress = int((xp_in_level / level_up_needed) * 100) if level_up_needed > 0 else 0
        bar = "█" * (progress // 10) + "░" * (10 - (progress // 10))

        from cogs.config_cog import config

        embed = discord.Embed(
            title=f"🎙️ Voice XP - {target.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        embed.add_field(name="Total XP", value=f"**{data['total_xp']:,}**", inline=True)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="Time in VC", value=self.format_time(data["total_minutes"]), inline=True)
        embed.add_field(name="Daily XP", value=f"{data['daily_xp']}/{config.max_daily_xp}", inline=True)
        embed.add_field(name="Weekly XP", value=f"{data['weekly_xp']:,}", inline=True)
        embed.add_field(name="Current Streak", value=f"**{data['streak']} days** 🔥", inline=True)
        embed.add_field(name="Progress to Next Level", value=f"{bar} {progress}%", inline=False)
        embed.add_field(name="XP Needed", value=f"{xp_needed} XP", inline=False)

        embed.set_footer(text=f"Earning {config.xp_per_minute} XP/min • Multipliers active")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="leaderboard", aliases=["lb", "top"], description="View voice XP leaderboard")
    async def leaderboard(self, ctx, type: str = "all"):
        """Show leaderboard for different time periods"""
        from cogs.database_cog import _db

        stat_map = {
            "all": "total_xp",
            "weekly": "weekly_xp",
            "monthly": "monthly_xp"
        }

        stat = stat_map.get(type.lower(), "total_xp")
        data = await _db.get_leaderboard(ctx.guild.id, stat, 10)

        if not data:
            await ctx.send("📊 No voice XP data yet! Join a voice channel with someone to start earning XP!")
            return

        title_map = {
            "total_xp": "🏆 All-Time Voice Leaders",
            "weekly_xp": "📊 Weekly Voice Champions",
            "monthly_xp": "🌙 Monthly Voice Masters"
        }

        embed = discord.Embed(
            title=title_map.get(stat, "Voice XP Leaderboard"),
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )

        description = ""
        for idx, row in enumerate(data, 1):
            member = ctx.guild.get_member(int(row["user_id"]))
            name = member.display_name if member else "Unknown"

            medal = {1: "👑 ", 2: "🥈 ", 3: "🥉 "}.get(idx, f"{idx}. ")
            time_str = self.format_time(row["total_minutes"])

            description += f"{medal}**{name}**\n"
            description += f"   Level {row['level']} • {row[stat]:,} XP • {time_str}\n\n"

        embed.description = description
        embed.set_footer(text="Use /leaderboard weekly or /leaderboard monthly for different rankings")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="top-weekly", description="View weekly voice XP leaderboard")
    async def top_weekly(self, ctx):
        """Shortcut for weekly leaderboard"""
        await self.leaderboard(ctx, "weekly")

    @commands.hybrid_command(name="top-monthly", description="View monthly voice XP leaderboard")
    async def top_monthly(self, ctx):
        """Shortcut for monthly leaderboard"""
        await self.leaderboard(ctx, "monthly")

    @commands.hybrid_command(name="multipliers", description="Show active XP multipliers")
    async def show_multipliers(self, ctx):
        """Display information about XP multipliers"""
        from cogs.config_cog import config
        tracker = self.bot.get_cog("VoiceTrackerCog")
        current_time_mult = tracker.get_time_multiplier() if tracker else 1.0

        embed = discord.Embed(
            title="✨ XP Multipliers Guide",
            description="Boost your XP earnings with these bonuses!",
            color=discord.Color.green()
        )

        # Streak multipliers
        streak_text = ""
        for days, mult in config.streak_multipliers.items():
            streak_text += f"**{days} days** → {mult}x XP\n"
        embed.add_field(name="🔥 Streak Bonuses", value=streak_text or "No streaks yet", inline=True)

        # Channel multipliers
        channel_text = ""
        for keyword, mult in list(config.channel_multipliers.items())[:5]:
            channel_text += f"**{keyword}** channels → {mult}x\n"
        embed.add_field(name="📢 Channel Bonuses", value=channel_text, inline=True)

        # Time multipliers
        time_text = f"**Current:** {current_time_mult}x\n"
        time_text += "**Morning** (6-12): 1.2x\n"
        time_text += "**Night** (22-2): 1.25x\n"
        time_text += "**Weekend**: 1.5x"
        embed.add_field(name="⏰ Time Bonuses", value=time_text, inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="test")
    async def test_command(self, ctx):
        """Test if bot is responding"""
        await ctx.send("✅ Bot is working! Join a voice channel with a friend for 2 minutes, then use `/voice`")


async def setup(bot):
    await bot.add_cog(UserCommandsCog(bot))