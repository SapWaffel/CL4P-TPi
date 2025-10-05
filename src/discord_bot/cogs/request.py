from discord.ext import commands
from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.util.check_online import check_status
from src.boot_service.boot_service import boot
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

class RequestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='request', help='Stellt eine Boot-Anfrage.')
    @commands.guild_only()
    async def request(self, ctx):
        # wenn !request start, dann a - wenn !request stop, dann b
        status = check_status()
        if status == "starting":
            await ctx.send(StringManager.get_string(StringType.ERROR, "response.request.deny", reason=StringManager.get_string(StringType.APPENDIX, "response.request.deny.starting")))
            RelevanceLogger.write_log_entry("cmd.request - failed (already booting)", ctx.author.id, LogType.INFO)
            return

        if ctx.message.content.lower().strip() == "!request start" | status == "offline":
            boot_result = boot(cooldown_seconds=15*60)
            if boot_result["success"]:
                await ctx.send(StringManager.get_string(StringType.SUCCESS, "response.request.success"))
                RelevanceLogger.write_log_entry("cmd.request - success", ctx.author.id, LogType.INFO)
            else:
                await ctx.send(StringManager.get_string(StringType.ERROR, "response.request.deny.generic", reason=boot_result["error"]))
                RelevanceLogger.write_log_entry(f"cmd.request - failed ({boot_result['error']})", ctx.author.id, LogType.INFO)
        elif ctx.message.content.lower().strip() == "!request stop" | status == "online":
            boot_result = boot()
            if boot_result["success"]:
                await ctx.send(StringManager.get_string(StringType.SUCCESS, "response.request.success"))
                RelevanceLogger.write_log_entry("cmd.request - success", ctx.author.id, LogType.INFO)
            else:
                await ctx.send(StringManager.get_string(StringType.ERROR, "response.request.deny.generic", reason=boot_result["error"]))
                RelevanceLogger.write_log_entry(f"cmd.request - failed ({boot_result['error']})", ctx.author.id, LogType.INFO)
        else:
            await ctx.send(StringManager.get_string(StringType.ERROR, "response.request.deny.generic", reason=StringManager.get_string(StringType.APPENDIX, "response.request.deny.boot_state")))
            RelevanceLogger.write_log_entry("cmd.request - failed (invalid state)", ctx.author.id, LogType.INFO)

async def setup(bot):
    await bot.add_cog(RequestCog(bot))