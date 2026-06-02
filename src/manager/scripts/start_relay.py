# src/manager/scripts/start_relay.py
import sys
import logging

from src.manager.service.boot import boot

logger = logging.getLogger(__name__)

def start_relay():
    try:
        logger.info("Starting relay...")
        boot()
        print("Relay started successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to start relay: {e}")
        return 1

if __name__ == "__main__":
    exit_code = start_relay()
    sys.exit(exit_code)