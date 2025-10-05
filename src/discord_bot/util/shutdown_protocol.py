from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

def shutdown_protocol():
    RelevanceLogger.write_log_entry("Shutting down the bot...", LogType.INFO)
    RelevanceLogger.write_log_entry("Goodbye!", LogType.INFO)
    RelevanceLogger.finalize_log_file()
    exit(0)