import discord
from discord import app_commands

from src.config_manager import StringManager, StringType
from src.models import RightsLevel
from src.util.db.database_manager import DatabaseManager

def get_rights_level(discord_id: int):
    return DatabaseManager.get("discord", "user", {"discord_id": int(discord_id)}, "rights_level")

def requre_rights(min_level: RightsLevel):
    """
    app_commands check for rights level
    usage:

    @app_commands.command(...)
    @app_commands.guilds(...)
    @require_rights(RightsLevel.ADMIN)
    async def my_command(interaction: discord.Interaction):
        ...
    """

    async def predicate(interaction: discord.Interaction) -> bool:
        rights_level = get_rights_level(interaction.user.id)

        # unknown user
        if not rights_level:
            await interaction.response.send_message(
                StringManager.get(StringType.WARN, "error.unknown_user"), ephemeral=True
            )
            return False

        # insufficient rights
        if rights_level < min_level:
            await interaction.response.send_message(
                StringManager.get(StringType.WARN, "error.no_permission"), ephemeral=True
            )
            return False

        return True

    return app_commands.check(predicate)