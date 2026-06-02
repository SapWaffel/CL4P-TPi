import threading
import logging
from src.discord_bot.bot import run
from src.manager.boot_manager import BootManager

logger = logging.getLogger(__name__)

def run_boot_manager():
    try:
        boot_manager = BootManager()
        boot_manager.watch_for_boot_request()
    except Exception as e:
        logger.error(f"Boot manager encountered an error: {e}")

if __name__ == "__main__":
    boot_manager_thread = threading.Thread(target=run_boot_manager, daemon=True)
    boot_manager_thread.start()
    logger.info("Boot manager started in background thread")

    run()