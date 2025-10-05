from discord.ext import commands
from src.config_manager import ConfigManager
from src.discord_bot.util.is_admin_on_guild import is_admin_on_guild
from src.discord_bot.util.check_online import check_status
from src.boot_service import boot_service
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

class BootCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.boot.admin_only = True
    
    @commands.command(name='boot', help='Boot-toggled CL4P-TP.')
    @commands.dm_only()
    async def boot(self, ctx):
        if not await is_admin_on_guild(self.bot, ctx.author.id):
            await ctx.send(ConfigManager.get_config("strings")["error"]["no_permission"])
            RelevanceLogger.write_log_entry(f"cmd.boot - failed (no permission)", ctx.author.id, LogType.INFO)
            return
        
        status = check_status()
        if status == "starting":
            await ctx.send(ConfigManager.get_config("strings")["response"]["boot"]["error"].replace("{error}", ConfigManager.get_config("strings")["response"]["request"]["deny"]["already_starting"]))
            RelevanceLogger.write_log_entry(f"cmd.boot - failed (already starting)", ctx.author.id, LogType.INFO)
            return
        
        boot_result = boot_service.boot()
        if boot_result["status"] == "success":
            await ctx.send(ConfigManager.get_config("strings")["response"]["boot"]["success"])
            RelevanceLogger.write_log_entry(f"cmd.boot - success", ctx.author.id, LogType.INFO)
        else:
            await ctx.send(ConfigManager.get_config("strings")["response"]["boot"]["error"].replace("{error}", boot_result["error"]))
            RelevanceLogger.write_log_entry(f"cmd.boot - failed ({boot_result['error']})", ctx.author.id, LogType.WARNING)

async def setup(bot):
    await bot.add_cog(BootCog(bot))