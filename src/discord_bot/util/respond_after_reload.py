from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

async def respond_after_reload(bot, response_data):
    channel_id = response_data["channel"]
    message_id = response_data["message"]

    user = response_data["user"]
    if user is not None:
        user = f"<@{user}> "

    try:
        channel = await bot.fetch_channel(channel_id)
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(content=StringManager.get_string(StringType.SUCCESS, "response.reload.success", user=user))
            RelevanceLogger.write_log_entry(f"Sent reload response message in channel {channel_id}.", "SYSTEM", LogType.INFO)
        except Exception as e:
            RelevanceLogger.write_log_entry(f"Failed to delete reload message {message_id} in channel {channel_id}: {e}", "SYSTEM", LogType.WARNING)
            await channel.send(StringManager.get_string(StringType.WARNING, "response.reload.partial_success", user=user, error=str(e)))
            return
    except Exception as e:
        RelevanceLogger.write_log_entry(f"Failed to fetch channel {channel_id} to send reload response: {e}", "SYSTEM", LogType.ERROR)
        return

    # reset config
    ConfigManager.merge_config(module="discord_bot", new_data={"reload_response": {"waiting_for_response": False,"user": None, "channel": None, "message": None}})

