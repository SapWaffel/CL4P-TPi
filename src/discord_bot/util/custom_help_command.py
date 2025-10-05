import discord
from discord.ext import commands
from src.discord_bot.util.is_admin_on_guild import is_admin_on_guild
import json
from src.config_manager import ConfigManager

MAINTENANCE = lambda: ConfigManager.get_config('discord_bot')["maintenance"]

class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        ctx = self.context
        embed = discord.Embed(title="CL4P-TP Bot Hilfe", description="Verfügbare Commands", color=discord.Color.blue())
        is_dm = isinstance(ctx.channel, discord.DMChannel)
        is_admin = await is_admin_on_guild(ctx.bot, ctx.author.id)

        if MAINTENANCE():
            # warning about maintenance mode
            embed.add_field(name="⚠️ Wartungsmodus aktiv", value="Der Bot befindet sich derzeit im Wartungsmodus. Einige Befehle sind möglicherweise nicht verfügbar.", inline=False)

        all_commands = []
        for cog, command_list in mapping.items():
            for cmd in command_list:
                # @hide_help
                if getattr(cmd, "hide_help", False):
                    continue
                # @admin_only
                if getattr(cmd, "admin_only", False) and not is_admin:
                    continue
                # @guild_only
                if getattr(cmd, "guild_only", False) and is_dm:
                    continue
                # @dm_only
                if getattr(cmd, "dm_only", False) and not is_dm:
                    continue
                all_commands.append(cmd)
        all_commands = await self.filter_commands(all_commands, sort=True)
        if all_commands:
            value = "\n".join(f"`!{cmd.name}`: {cmd.help or 'Keine Beschreibung'}" for cmd in all_commands)
            embed.add_field(name="Befehle", value=value, inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)
