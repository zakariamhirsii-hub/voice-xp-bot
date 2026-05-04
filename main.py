import discord
from discord.ext import commands
import os
import asyncio
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Get token from environment variable
TOKEN = os.environ.get("DISCORD_TOKEN")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    """Called when bot is ready"""
    print("\n" + "="*60)
    print(f"✅ VOICE XP BOT IS ONLINE!")
    print(f"📡 Logged in as: {bot.user.name}")
    print(f"🌐 Connected to {len(bot.guilds)} server(s)")
    print("="*60)
    print("\n📋 LOADED FEATURES:")
    print("  • Voice XP Tracking")
    print("  • Streaks & Multipliers")
    print("  • Daily/Weekly Quests")
    print("  • Achievements & Titles")
    print("  • Multiple Leaderboards")
    print("="*60)
    print("\n📋 COMMANDS:")
    print("  /voice - Your stats")
    print("  /leaderboard - All-time top")
    print("  /leaderboard weekly - Weekly top")
    print("  /top-weekly - Weekly shortcut")
    print("  /top-monthly - Monthly shortcut")
    print("  /multipliers - Show bonuses")
    print("  !test - Test bot")
    print("  !give-xp @user 100 - Admin")
    print("  !reset-xp @user - Admin")
    print("  !xp-config - Admin")
    print("="*60 + "\n")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")


@bot.command(name="test")
async def test_command(ctx):
    """Simple test command"""
    await ctx.send("✅ Bot is working! Join a voice channel with a friend to earn XP!")


async def load_cogs():
    """Load all cogs"""
    cogs = [
        "cogs.config_cog",
        "cogs.database_cog",
        "cogs.tracker_cog",
        "cogs.user_cmds",
        "cogs.admin_cmds"
    ]

    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")


async def main():
    """Main entry point"""
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERROR: DISCORD_TOKEN environment variable not set!")
        print("📍 Set it in Render dashboard or create .env file locally")
        print("📍 Get your token from: https://discord.com/developers/applications")
    else:
        print("🚀 Starting Voice XP Bot...")
        asyncio.run(main())