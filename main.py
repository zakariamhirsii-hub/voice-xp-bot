import discord
from discord.ext import commands
import os
import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# IMPORTANT: Get token from environment variable
TOKEN = os.environ.get("DISCORD_TOKEN")

# Check if token is missing
if not TOKEN:
    print("❌ ERROR: DISCORD_TOKEN environment variable not set!")
    print("📍 Set it in Render dashboard: Environment Variables → DISCORD_TOKEN")
    exit(1)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("\n" + "="*50)
    print(f"✅ VOICE XP BOT IS ONLINE!")
    print(f"📡 Logged in as: {bot.user.name}")
    print(f"🌐 Connected to {len(bot.guilds)} server(s)")
    print("="*50 + "\n")
    
    await bot.tree.sync()
    print("✅ Slash commands synced!")

@bot.command(name="test")
async def test_command(ctx):
    await ctx.send("✅ Bot is working!")

@bot.hybrid_command(name="voice")
async def voice_stats(ctx):
    await ctx.send("🎙️ Voice XP system active!")

async def load_cogs():
    try:
        await bot.load_extension("cogs.tracker_cog")
        print("✅ Loaded tracker_cog")
    except Exception as e:
        print(f"❌ Failed to load tracker_cog: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    print("🚀 Starting Voice XP Bot...")
    asyncio.run(main())
