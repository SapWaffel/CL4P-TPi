# send message to user who requested reboot after bot has restarted
import discord
from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

async def respond_after_reboot(bot, user):
    if user is None:
        return
    
    user_obj = await bot.fetch_user(user)
    if user_obj is None:
        return
    
    await user_obj.send(StringManager.get_string(StringType.SUCCESS, "response.reload.success"))
    RelevanceLogger.write_log_entry(f"respond_after_reboot - sent confirmation to user {user}", "SYSTEM", LogType.INFO)

    # reset config
    ConfigManager.merge_config(module="discord_bot", new_data={"restart_response": {"waiting_for_response": False,"user": None}})