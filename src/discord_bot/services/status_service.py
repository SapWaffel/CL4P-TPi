# request status of host_type and host_name from MongoDB
import logging
from src.util.db.mongo_client import get_mongo_client

logger = logging.getLogger(__name__)

class StatusService:
    def __init__(self):
        mongo_client = get_mongo_client()
        self.host_db = mongo_client.get_db("host")

    def get_boot_status(self, host_type: str, hostname: str) -> dict:
        try:
            collection = self.host_db[host_type]
            host = collection.find_one({"hostname": hostname})

            if not host:
                return {"success": False, "message": "Host not found"}

            boot_data = host.get("boot", {})
            status = boot_data.get("status", "unknown")
            last_update = boot_data.get("last_update", "unknown")

            return {
                "success": True,
                "status": status,
                "last_update": last_update,
                "hostname": hostname,
                "host_type": host_type
            }

        except Exception as e:
            logger.error(f"Error occurred while fetching boot status for {hostname}: {e}")
            return {"success": False, "message": "Error occurred while fetching boot status"}
