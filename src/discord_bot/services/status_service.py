# request status of host_type and host_name from MongoDB
import logging
from src.util.db.mongo_client import get_mongo_client

from src.config_manager import StringManager, StringType

logger = logging.getLogger(__name__)

class StatusService:
    def __init__(self, host_type="hardware", hostname="claptp"):
        mongo_client = get_mongo_client()
        self.host_db = mongo_client.get_db("host")
        self.collection = self.host_db[host_type]
        self.host_type = host_type
        self.hostname = hostname

    def get_boot_status(self) -> dict:
        try:
            host = self.collection.find_one({"hostname": self.hostname})

            if not host:
                logger.warning(f"No host found with hostname: {self.hostname}")
                return {"success": False, "message": "Host not found"}

            boot_data = host.get("boot", {})
            status = boot_data.get("status", "unknown")
            last_update = boot_data.get("last_update", "unknown")

            return {
                "success": True,
                "status": status,
                "last_update": last_update,
                "hostname": self.hostname,
                "host_type": self.host_type
            }

        except Exception as e:
            logger.error(f"Error occurred while fetching boot status for {self.hostname}: {e}")
            return {"success": False, "message": "Error occurred while fetching boot status"}
