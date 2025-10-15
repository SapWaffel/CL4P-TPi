import discord
from discord.ext import commands
from discord import app_commands

from typing import Literal
import time

from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.util.check_status import check_status
from src.boot_service.boot_service import boot
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType
from src.discord_bot.constant import GUILD_ID

class RequestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(GUILD_ID)
    @app_commands.command(name="request", description="Stellt eine Anfrage zum Starten/Stoppen von CL4P-TP.")
    async def request(
        self,
        interaction: discord.Interaction,
        action: Literal["start", "stop"]
    ):
        await interaction.response.defer()
        
        ## Check restrictions
        check = await self.check_restrictions(action)
        if check["success"] == False:
            await interaction.followup.send(StringManager.get_string(StringType.ERROR, "response.request.deny.generic", reason=check["error"]))
            return
        
        try:
            boot_success = boot(cooldown_seconds=ConfigManager.get_config('_global')['boot_cooldown_seconds'])
            if boot_success["success"]:
                RelevanceLogger.write_log_entry(f"cmd.request - success to {action}", interaction.user, LogType.INFO)
                await interaction.followup.send(StringManager.get_string(StringType.SUCCESS, f"response.request.success.{action}"))
            else:
                RelevanceLogger.write_log_entry(f"cmd.request - failed to {action}: {boot_success['error']}", interaction.user, LogType.WARNING)
                await interaction.followup.send(StringManager.get_string(StringType.ERROR, "error.generic"))
        except Exception as e:
            RelevanceLogger.write_log_entry(f"cmd.request - failed to {action}: {e}", interaction.user, LogType.ERROR)
            await interaction.followup.send(StringManager.get_string(StringType.ERROR, "error.generic"))
            return

    async def check_restrictions(self, action):
        status = check_status()
        b_state = status=="online"

        b_action = action=="start"
        # Boot state = requested action
        if b_state == b_action:
            RelevanceLogger.write_log_entry(f"sys.restrictions - failed (already {status})", "SYSTEM", LogType.INFO)
            return {"success": False, "error": StringManager.get_string(StringType.APPENDIX, f"response.request.deny.reasons.boot_state", state=status)}
        
        # Already starting
        if status == "starting":
            RelevanceLogger.write_log_entry(f"sys.restrictions - failed (already starting)", "SYSTEM", LogType.INFO)
            return {"success": False, "error": StringManager.get_string(StringType.APPENDIX, "response.request.deny.reasons.starting")}

        # Load restrictions
        restrictions = ConfigManager.get_config('_global')['boot_restrictions']
        
        # No restrictions
        if not restrictions['enabled']:
            RelevanceLogger.write_log_entry(f"sys.restrictions - pass (no restrictions)", "SYSTEM", LogType.INFO)
            return {"success": True}
        
        # Always allowed
        if restrictions['always_allow'][f'{action}']:
            RelevanceLogger.write_log_entry(f"sys.restrictions - pass (always allowed)", "SYSTEM", LogType.INFO)
            return {"success": True}
    
        # Single Shot
        if restrictions['single_shot'][f'{action}']:
            restrictions['single_shot'][f'{action}'] = False
            ConfigManager.merge_config(module='_global', new_data={'boot_restrictions': restrictions})
            RelevanceLogger.write_log_entry(f"sys.restrictions - pass (single shot)", "SYSTEM", LogType.INFO)
            return {"success": True}
        
        # Work hours
        if len(restrictions['work_hours']) > 0:
            hour, min = map(int, time.strftime("%H %M").split())
            weekday = time.strftime("%A").lower()

            ## Check if today is a work day
            if not any(weekday in entry['days'] for entry in restrictions['work_hours']):
                RelevanceLogger.write_log_entry(f"sys.restrictions - failed (not a work day)", "SYSTEM", LogType.INFO)
                return {"success": False, "error": StringManager.get_string(StringType.APPENDIX, "response.request.deny.reasons.no_workday")}
            
            ## Check for time
            for entry in restrictions['work_hours']:
                if weekday in entry['days']:
                    start_h, start_m = map(int, entry['start'].split(':'))
                    end_h, end_m = map(int, entry['end'].split(':'))
                    if (hour > start_h or (hour == start_h and min >= start_m)) and (hour < end_h or (hour == end_h and min <= end_m)):
                        RelevanceLogger.write_log_entry(f"sys.restrictions - pass (within work hours)", "SYSTEM", LogType.INFO)
                        return {"success": True}
                    RelevanceLogger.write_log_entry(f"sys.restrictions - failed (outside work hours)", "SYSTEM", LogType.INFO)
                    return {"success": False, "error": StringManager.get_string(StringType.APPENDIX, "response.request.deny.reasons.working_hours")}    

        RelevanceLogger.write_log_entry(f"sys.restrictions - pass (passed all checks)", "SYSTEM", LogType.INFO)
        return {"success": True}

async def setup(bot):
    await bot.add_cog(RequestCog(bot))