from src.config_manager import ConfigManager

GUILD_ID = ConfigManager.get_config('discord_bot')['guild_id']

async def is_admin_on_guild(bot, user_id):
    guild = bot.get_guild(int(GUILD_ID))
    if not guild:
        return False
    member = guild.get_member(user_id)
    if not member:
        return False
    return member.guild_permissions.administrator