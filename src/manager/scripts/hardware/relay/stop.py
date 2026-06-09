# TODO: Replace with ProxMox implementation w/ bulk actions

from src.manager.service import relay
import logging

logger = logging.getLogger(__name__)


def run():
    try:
        return relay.boot()
    except Exception as e:
        return {"success": False, "error": {"type": "unknown", "e": str(e)}}

run()