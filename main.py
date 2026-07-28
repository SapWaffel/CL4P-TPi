import threading
import logging
from time import time
from src.discord_bot.bot import run
from src.manager.boot_manager import BootManager

from src.config_manager import ConfigManager


logger = logging.getLogger(__name__)

BOOT_MANAGER_RESTART_DELAY = 5

def run_boot_manager():
    while True:
        try:
            boot_manager = BootManager()
            boot_manager.watch_for_boot_request()
        except Exception as e:
            logger.error(f"Boot manager crashed, restarting in {BOOT_MANAGER_RESTART_DELAY}s: {e}", exc_info=True)
        time.sleep(BOOT_MANAGER_RESTART_DELAY)

if __name__ == "__main__":

    try:
        ConfigManager()
    except Exception as e:
        logger.error(f"Error initializing configuration: {e}")
        exit(1)

    boot_manager_thread = threading.Thread(target=run_boot_manager, daemon=True)
    boot_manager_thread.start()
    logger.info("Boot manager started in background thread")

    run()