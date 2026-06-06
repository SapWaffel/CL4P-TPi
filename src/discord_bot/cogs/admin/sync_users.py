import discord
from discord.ext import commands
import logging

from src.config_manager import ConfigManager
from src.discord_bot.services.user_service import UserService
from src.util.db.database_manager import DatabaseManager

logger = logging.getLogger(__name__)
GUILD_ID = discord.Object(id=int(ConfigManager.get("discord.guild_id")))

class UserSyncCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_service = UserService()
    
    @commands.Cog.listener()
    async def on_ready(self):
        
        try:
            guild = self.bot.get_guild(int(ConfigManager.get("discord.guild_id")))

            if guild is None:
                logger.error(f"Guild with ID {GUILD_ID.id} not found.")
                return
            
            # fetch all members
            members = [member async for member in guild.fetch_members(limit=None)]

            # sync to database
            synced = 0
            for member in members:
                if not member.bot:  # ignore bots
                    # Check if user already exists
                    existing_user = DatabaseManager.get("discord", "user", {"discord_id": member.id})
                    if existing_user:
                        logger.debug(f"User {member.name} already in database, skipping.")
                        continue
                    
                    # Sync only new users
                    result = self.user_service.sync_or_create_user(
                        discord_id=member.id,
                        username=member.name,
                        avatar=member.avatar.url if member.avatar else None,
                        roles=[str(role.id) for role in member.roles if role.id != guild.id]  # exclude @everyone role
                    )
                    if result["success"]:
                        synced += 1
                        logger.info(f"Synced new user: {member.name}")
                        
            logger.info(f"Synchronized {synced} new users to the database.")

        except Exception as e:
            logger.error(f"Error occurred while synchronizing users: {e}")

async def setup(bot):
    await bot.add_cog(UserSyncCog(bot))