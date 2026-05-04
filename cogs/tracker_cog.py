import discord
from discord.ext import commands, tasks
from datetime import datetime


class VoiceTrackerCog(commands.Cog):
    """Tracks voice state changes and awards XP"""

    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}
        self.checker.start()

    def get_time_multiplier(self) -> float:
        """Get multiplier based on time of day"""
        from cogs.config_cog import config

        hour = datetime.now().hour
        weekday = datetime.now().weekday()

        # Weekend bonus
        if weekday >= 5:  # Saturday (5) or Sunday (6)
            return config.time_multipliers["weekend"][2]

        # Morning bonus
        if 6 <= hour < 12:
            return 1.2

        # Night bonus
        if 22 <= hour or hour < 2:
            return 1.25

        return 1.0

    def get_channel_multiplier(self, channel_name: str) -> float:
        """Get multiplier based on channel name keywords"""
        from cogs.config_cog import config

        name_lower = channel_name.lower()
        for keyword, multiplier in config.channel_multipliers.items():
            if keyword in name_lower:
                return multiplier
        return 1.0

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        """Track voice state changes"""
        if member.bot:
            return

        key = f"{member.guild.id}:{member.id}"
        from cogs.config_cog import config

        # User joined voice channel
        if after.channel and not before.channel:
            # Check AFK channel
            if any(afk in after.channel.name.lower() for afk in config.afk_channel_names):
                return

            self.sessions[key] = {
                "start": datetime.now(),
                "member": member,
                "multiplier": self.get_channel_multiplier(after.channel.name)
            }
            print(f"🎤 {member.name} joined {after.channel.name}")

        # User left voice channel
        elif not after.channel and before.channel and key in self.sessions:
            session = self.sessions.pop(key)
            await self._process_session(session)

        # User moved channels
        elif after.channel and before.channel and before.channel.id != after.channel.id and key in self.sessions:
            session = self.sessions.pop(key)
            await self._process_session(session)

            # Start new session
            if not any(afk in after.channel.name.lower() for afk in config.afk_channel_names):
                self.sessions[key] = {
                    "start": datetime.now(),
                    "member": member,
                    "multiplier": self.get_channel_multiplier(after.channel.name)
                }

    async def _process_session(self, session: dict):
        """Process a voice session and award XP"""
        minutes = int((datetime.now() - session["start"]).total_seconds() / 60)

        if minutes < 1:
            return

        member = session["member"]
        from cogs.config_cog import config

        # Check AFK conditions
        voice_state = member.voice
        if voice_state and voice_state.channel:
            humans = [m for m in voice_state.channel.members if not m.bot]

            # Check if alone
            if len(humans) <= 1 and not config.allow_alone:
                print(f"🚫 {member.name} was alone - No XP")
                return

            # Check if muted
            if voice_state.self_mute and not config.allow_muted:
                print(f"🔇 {member.name} was muted - No XP")
                return

            # Check if deafened
            if voice_state.self_deaf and not config.allow_deafened:
                print(f"🦻 {member.name} was deafened - No XP")
                return

        # Calculate final XP with multipliers
        channel_mult = session.get("multiplier", 1.0)
        time_mult = self.get_time_multiplier()
        total_multiplier = channel_mult * time_mult

        from cogs.database_cog import _db
        await _db.add_queue(member.id, member.guild.id, minutes, total_multiplier)

        print(f"✅ {member.name} +{int(minutes * 10 * total_multiplier)} XP ({minutes}min, x{total_multiplier:.1f})")

    @tasks.loop(seconds=30)
    async def checker(self):
        """Check for AFK users and process their sessions"""
        for key, session in list(self.sessions.items()):
            member = session["member"]
            voice_state = member.voice

            if voice_state and voice_state.channel:
                from cogs.config_cog import config

                humans = [m for m in voice_state.channel.members if not m.bot]
                is_afk = (
                    (len(humans) <= 1 and not config.allow_alone) or
                    (voice_state.self_mute and not config.allow_muted) or
                    (voice_state.self_deaf and not config.allow_deafened)
                )

                if is_afk:
                    print(f"🔍 AFK detected: {member.name}")
                    await self._process_session(session)
                    del self.sessions[key]

    @checker.before_loop
    async def before_checker(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(VoiceTrackerCog(bot))