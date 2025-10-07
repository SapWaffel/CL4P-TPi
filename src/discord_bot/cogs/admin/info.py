# 4 later 
# save hard/software info to mqtt before

from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

async def setup(bot):
    RelevanceLogger.write_log_entry("Cog 'info' not implemented yet.", "SYSTEM", LogType.INFO)