from src.manager.service import relay
import logging

logger = logging.getLogger(__name__)

def __init__():
    try:
        return relay.boot()
    except Exception as e:
        return {"success": False, "error": {"type": "unknown", "e": str(e)}}
