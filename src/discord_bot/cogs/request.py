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

        status = check_status()
        
        # Restrict while starting
        if status == "starting":
            await ctx.send(StringManager.get_string(StringType.WARNING, "response.request.deny.generic", reason=StringManager.get_string(StringType.APPENDIX, "response.request.deny.reason.starting")))
            RelevanceLogger.write_log_entry("cmd.request - failed (already booting)", ctx.author, LogType.INFO)
            return
        
        # Get argument
        argument = ctx.message.content.lower().strip().split("!request ")[1] if len(ctx.message.content.lower().strip().split("!request ")) > 1 else None
        # No args
        if argument is None:
            await ctx.send(StringManager.get_string(StringType.ERROR, "response.request.deny.generic", reason=StringManager.get_string(StringType.APPENDIX, "response.request.deny.no_args")))
            RelevanceLogger.write_log_entry("cmd.request - failed (no args)", ctx.author, LogType.INFO)
            return
        # Invalid args
        if argument not in ["start", "stop"]:
            await ctx.send(StringManager.get_string(StringType.ERROR, "response.request.deny.generic", reason=StringManager.get_string(StringType.APPENDIX, "response.request.deny.invalid_arg")))
            RelevanceLogger.write_log_entry("cmd.request - failed (invalid arg)", ctx.author, LogType.INFO)
            return
        
        # Check restrictions
        restrictions = self.check_restrictions(ctx, argument)
        if not restrictions["success"]:
            await ctx.send(StringManager.get_string(StringType.ERROR, "response.request.deny.generic", reason=StringManager.get_string(StringType.APPENDIX, f"response.request.deny.reasons.{restrictions['error']}")))
            RelevanceLogger.write_log_entry(f"cmd.request - failed", ctx.author, LogType.INFO)
            return

        # boolean for start/stop
        B_action = argument == "start"
        B_state = status == "online"

        # Reject
        if B_action == B_state:
            await ctx.send(StringManager.get_string(StringType.ERROR, "response.request.deny.generic", reason=StringManager.get_string(StringType.APPENDIX, "response.request.deny.invalid", state=status)))
            RelevanceLogger.write_log_entry(f"cmd.request - failed (already {status})", ctx.author, LogType.INFO)
            return
        
        # Boot
        boot_success = boot(cooldown_seconds=ConfigManager.get_config('_global')["boot_cooldown_seconds"])
        if boot_success["success"]:
            try:
                boot_success = boot(cooldown_seconds=ConfigManager.get_config('_global')["boot_cooldown_seconds"])
                if boot_success["success"]:
                    RelevanceLogger.write_log_entry(f"cmd.request - success (request to {argument})", ctx.author, LogType.INFO)
                    await ctx.send(StringManager.get_string(StringType.SUCCESS, "response.request.success.generic", action=StringManager.get_string(StringType.APPENDIX, f"response.request.success.{argument}")))
                    return
                else:
                    await ctx.send(StringManager.get_string(StringType.ERROR, "response.request.deny.generic", reason=boot_success['error']))
                    RelevanceLogger.write_log_entry(f"cmd.request - failed ({boot_success['error']})", ctx.author, LogType.INFO)
                    return
            except Exception as e:
                await ctx.send(StringManager.get_string(StringType.ERROR, "response.request.deny.generic", reason=str(e)))
                RelevanceLogger.write_log_entry(f"cmd.request - failed ({str(e)})", ctx.author, LogType.INFO)
                return
        else:
            await ctx.send(StringManager.get_string(StringType.ERROR, "response.request.deny.generic", reason=StringManager.get_string(StringType.APPENDIX, f"response.request.deny.reasons.{boot_success['error']}")))
            RelevanceLogger.write_log_entry(f"cmd.request - failed ({boot_success['error']})", ctx.author, LogType.INFO)

    def check_restrictions(self, ctx, action):
        restrictions = ConfigManager.get_config('_global')['boot_restrictions']
        
        # No restrictions
        if not restrictions['enabled']:
            RelevanceLogger.write_log_entry("No boot restrictions set", "SYSTEM", LogType.INFO)
            return {"success": True}
        
        # Always allowed
        if restrictions['always_allow'][f'{action}']:
            RelevanceLogger.write_log_entry(f"Always allowed: {action}", "SYSTEM", LogType.INFO)
            return {"success": True}

        # Single shot
        if restrictions['single_shot'][f'{action}']:
            restrictions['single_shot'][f'{action}'] = False
            ConfigManager.merge_config('_global', {'boot_restrictions': restrictions})
            RelevanceLogger.write_log_entry(f"Single shot restriction applied for {action}", "SYSTEM", LogType.INFO)
            return {"success": True}

        # Working hours
        if len(restrictions['working_hours']) == 0:
            return {"success": True}
        else:
            hour = int(ctx.message.created_at.strftime("%H"))
            min = int(ctx.message.created_at.strftime("%M"))
            weekday = int(ctx.message.created_at.strftime("%w")) # 0 = Sunday, 6 = Saturday

            # check for weekday rule
            if not any(weekday in entry['days'] for entry in restrictions['working_hours']):
                RelevanceLogger.write_log_entry(f"Boot request denied (outside working hours): {action}", "SYSTEM", LogType.INFO)
                return {"success": False, "error": "working_hours"}
            
            # check for time rule
            for entry in restrictions['working_hours']:
                if weekday in entry['days']:
                    start_h, start_m = map(int, entry['start'].split(":"))
                    end_h, end_m = map(int, entry['end'].split(":"))
                    if (hour > start_h or (hour == start_h and min >= start_m)) and (hour < end_h or (hour == end_h and min <= end_m)):
                        return True
                    RelevanceLogger.write_log_entry(f"Boot request denied (outside working hours): {action}", "SYSTEM", LogType.INFO)
                    return {"success": False, "error": "working_hours"}

        return {"success": False, "error": "no_allowance"}

async def setup(bot):
    await bot.add_cog(RequestCog(bot))