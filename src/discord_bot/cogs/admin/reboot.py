from discord.ext import commands
from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.util.is_admin_on_guild import is_admin_on_guild
from src.discord_bot.util.check_online import check_status
from src.boot_service import boot_service
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

class RebootCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reboot.admin_only = True

    @commands.command(name='reboot', help='Rebooted CL4P-TP.')
    @commands.dm_only()
    async def reboot(self, ctx):
        if not await is_admin_on_guild(self.bot, ctx.author.id):
            await ctx.send(StringManager.get_string(StringType.ERROR, "error.no_permission"))
            RelevanceLogger.write_log_entry(f"cmd.reboot - failed (no permission)", ctx.author, LogType.INFO)
            return
        
        status = check_status()
        if status == "starting":
            await ctx.send(StringManager.get_string(StringType.ERROR, "response.reboot.error").replace("{error}", StringManager.get_string(StringType.ERROR, "response.request.deny.starting")))
            RelevanceLogger.write_log_entry(f"cmd.reboot - failed (already starting)", ctx.author, LogType.INFO)
            return
            
        boot_result = boot_service.reboot()
        if boot_result["success"] == True:
            await ctx.send(StringManager.get_string(StringType.SUCCESS, "response.reboot.success"))
            RelevanceLogger.write_log_entry(f"cmd.reboot - success", ctx.author, LogType.INFO)
        else:
            await ctx.send(StringManager.get_string(StringType.ERROR, "response.reboot.error").replace("{error}", boot_result["error"]))
            RelevanceLogger.write_log_entry(f"cmd.reboot - failed ({boot_result['error']})", ctx.author, LogType.WARNING)

async def setup(bot):
    await bot.add_cog(RebootCog(bot))