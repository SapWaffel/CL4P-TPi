from discord.ext import commands
from src.mqtt import MqttManager
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType
from src.config_manager import ConfigManager
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='status', help='Fragt CL4P-TPs aktuellen Status ab.')
    async def status(self, ctx):
        status = MqttManager.read("status")
        if status == "starting": status = "am booten"
        await ctx.send(ConfigManager.get_config("strings")["response"]["status"].replace("{status}", status))
        RelevanceLogger.write_log_entry(f"cmd.status - success ({status})", ctx.author.id, LogType.INFO)

async def setup(bot):
    await bot.add_cog(StatusCog(bot))
    RelevanceLogger.write_log_entry("cog.status - loaded", "system", LogType.INFO)