import discord
from discord.ext import commands
import sqlite3


class AdminCommandsCog(commands.Cog):
    """Administrative commands for the XP system"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="give-xp")
    @commands.has_permissions(administrator=True)
    async def give_xp(self, ctx, member: discord.Member, amount: int):
        """Manually give XP to a user (Admin only)"""
        from cogs.database_cog import _db

        # Add to queue (rough conversion: 10 XP per minute)
        await _db.add_queue(member.id, ctx.guild.id, amount // 10, 1.0)

        embed = discord.Embed(
            title="✅ XP Added",
            description=f"Added **{amount} XP** to {member.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="reset-xp")
    @commands.has_permissions(administrator=True)
    async def reset_xp(self, ctx, member: discord.Member):
        """Reset a user's XP (Admin only)"""
        from cogs.database_cog import _db

        with sqlite3.connect(_db.db_path) as conn:
            conn.execute('''
                UPDATE xp_users
                SET total_xp = 0,
                    total_minutes = 0,
                    daily_xp = 0,
                    weekly_xp = 0,
                    monthly_xp = 0,
                    streak = 0,
                    level = 0
                WHERE user_id = ? AND guild_id = ?
            ''', (str(member.id), str(ctx.guild.id)))

        embed = discord.Embed(
            title="🔄 XP Reset",
            description=f"Reset all XP for {member.mention}",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command(name="xp-config")
    @commands.has_permissions(administrator=True)
    async def xp_config(self, ctx, setting: str = None, value: str = None):
        """View or change XP system configuration (Admin only)"""
        from cogs.config_cog import config

        # Show current config
        if not setting:
            embed = discord.Embed(title="⚙️ XP System Configuration", color=discord.Color.blue())
            embed.add_field(name="XP per Minute", value=f"{config.xp_per_minute} XP", inline=True)
            embed.add_field(name="Daily Limit", value=f"{config.max_daily_xp} XP", inline=True)
            embed.add_field(name="Allow Muted", value=f"{config.allow_muted}", inline=True)
            embed.add_field(name="Allow Deafened", value=f"{config.allow_deafened}", inline=True)
            embed.add_field(name="Allow Alone", value=f"{config.allow_alone}", inline=True)
            embed.add_field(name="AFK Channels", value=", ".join(config.afk_channel_names), inline=False)
            await ctx.send(embed=embed)
            return

        # Update settings
        if setting == "rate" and value:
            config.xp_per_minute = int(value)
            await ctx.send(f"✅ XP rate set to {value} XP per minute")

        elif setting == "allow_muted" and value in ["true", "false"]:
            config.allow_muted = value == "true"
            await ctx.send(f"✅ Muted users {'can' if config.allow_muted else 'cannot'} earn XP")

        elif setting == "allow_deafened" and value in ["true", "false"]:
            config.allow_deafened = value == "true"
            await ctx.send(f"✅ Deafened users {'can' if config.allow_deafened else 'cannot'} earn XP")

        elif setting == "allow_alone" and value in ["true", "false"]:
            config.allow_alone = value == "true"
            await ctx.send(f"✅ Users {'can' if config.allow_alone else 'cannot'} earn XP when alone")

        else:
            await ctx.send("❌ Invalid setting. Use:\n"
                          "`!xp-config` - View settings\n"
                          "`!xp-config rate 15` - Change XP rate\n"
                          "`!xp-config allow_muted true` - Allow muted users\n"
                          "`!xp-config allow_deafened true` - Allow deafened users\n"
                          "`!xp-config allow_alone true` - Allow solo XP")


async def setup(bot):
    await bot.add_cog(AdminCommandsCog(bot))