import logging
from datetime import datetime
from src.models import BootRequestStatus, RightsLevel
from src.discord_bot.services.restriction_service import RestrictionService
from src.util.db.mongo_client import get_mongo_client

logger = logging.getLogger(__name__)


class BootRequestHandler:
    def __init__(
        self,
        host_type="hardware",
        host_name="claptp",
        cooldown_seconds: int = 300,
        rights_level: RightsLevel = RightsLevel.BASIC,
    ):
        self.restriction_service = RestrictionService()

        mongo_client = get_mongo_client()
        self.host_db = mongo_client.get_db("host")
        self.host_collection = self.host_db[host_type]

        self.discord_db = mongo_client.get_db("discord")
        self.boot_restriction_collection = self.discord_db["boot_restriction"]

        self.host_type = host_type
        self.host_name = host_name
        self.cooldown_seconds = cooldown_seconds
        self.rights_level = rights_level

    def handle_request(self, action: str) -> dict:
        try:
            if action not in ["start", "stop", "restart"]:
                return {"success": False, "reason": "invalid_action"}
            
            # 1) Check host status
            status_result = self.check_host_status(action)
            if not status_result["success"]:
                return status_result

            # 2) Check restrictions
            if self.rights_level != RightsLevel.ADMIN:
                restriction_result = self.check_restrictions(action)
                if not restriction_result["success"]:
                    return restriction_result
                if restriction_result["status"] == BootRequestStatus.REJECTED.value:
                    return restriction_result

            # 3) Check cooldown
            cooldown_result = self.check_cooldown()
            if not cooldown_result["success"]:
                return cooldown_result

            # 4) Set boot.request flag in MongoDB
            self.host_collection.update_one(
                {"hostname": self.host_name},
                {
                    "$set": {
                        "boot.request.requested": True,
                        "boot.request.action": action,
                        "boot.request.timestamp": datetime.now(),
                    }
                },
            )

            return {
                "success": True,
                "status": BootRequestStatus.APPROVED.value,
                "reason": "All checks passed",
            }

        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            return {"success": False, "error": f"Unexpected error: {e}"}

    def check_host_status(self, action: str) -> dict:
        try:
            host = self.host_collection.find_one({"hostname": self.host_name})

            if not host:
                logger.warning(f"Host {self.host_name} not found in database.")
                return {"success": False, "reason": "unknown_host"}

            current_status = host.get("boot", {}).get("status", "unknown")

            if action == "restart" and current_status != "on":
                return {"success": False, "reason": "boot_state", "state": current_status}

            if action == "start" and current_status == "on":
                return {"success": False, "reason": "boot_state", "state": "online"}

            if action == "stop" and current_status == "off":
                return {"success": False, "reason": "boot_state", "state": "offline"}

            if current_status == "starting":
                return {"success": False, "reason": "starting"}

            return {"success": True, "status": BootRequestStatus.APPROVED.value}

        except Exception as e:
            logger.error(f"Error occurred while checking host status: {e}")
            return {"success": False, "reason": "unknown_error", "error": str(e)}

    def check_restrictions(self, action: str) -> dict:
        try:
            result = self.restriction_service.get_all_restrictions()
            if not result["success"]:
                logger.error(f"Error fetching restrictions: {result.get('error', 'unknown')}")
                return {"success": False, "reason": "unknown_error", "error": result.get("error", "unknown")}

            restrictions = result["restrictions"]

            # 1) ALWAYS_ALLOW
            for restriction in restrictions:
                if restriction["type"] == "ALWAYS_ALLOW" and restriction["enabled"]:
                    if restriction["config"].get(action, False):
                        return {
                            "success": True,
                            "status": BootRequestStatus.APPROVED.value,
                            "reason": "ALWAYS_ALLOW restriction",
                        }

            # 2) SINGLE_SHOT
            for restriction in restrictions:
                if restriction["type"] == "SINGLE_SHOT" and restriction["enabled"]:
                    if restriction["config"].get(action, False):
                        # disable SINGLE_SHOT restriction after use
                        self.restriction_service.collection.update_one(
                            {"_id": restriction["_id"]}, {"$set": {"enabled": False}}
                        )
                        return {
                            "success": True,
                            "status": BootRequestStatus.APPROVED.value,
                            "reason": "SINGLE_SHOT restriction",
                        }

            # 3) WORKING_HOURS
            for restriction in restrictions:
                if restriction["type"] == "WORKING_HOURS" and restriction["enabled"]:
                    if restriction["config"].get(action, False):
                        if self._is_within_working_hours(restriction["config"]):
                            return {
                                "success": True,
                                "status": BootRequestStatus.APPROVED.value,
                                "reason": "WORKING_HOURS restriction",
                            }
            return {
                "success": True,
                "status": BootRequestStatus.REJECTED.value,
                "reason": "No applicable restrictions allowed the request",
            }

        except Exception as e:
            logger.error(
                f"Error occurred while handling boot request: {e}"
            )
            return {"success": False, "reason": "unknown_error", "error": str(e)}

    def check_cooldown(self) -> dict:
        try:
            last_request = self.host_collection.find_one(
                {"hostname": self.host_name},
                sort=[("boot.request.timestamp", -1)]
            )
            
            if not last_request: 
                return {"success": True}

            # Get last timestamp
            last_timestamp = last_request.get("boot", {}).get("request", {}).get("timestamp")
            if not last_timestamp:
                return {"success": True}

            # Calculate elapsed time
            now = datetime.now()
            elapsed = (now - last_timestamp).total_seconds()
            
            if elapsed < self.cooldown_seconds:
                remaining = self.cooldown_seconds - int(elapsed)
                return {
                    "success": False,
                    "reason": "cooldown",
                    "m": remaining // 60,
                    "s": remaining % 60
                }
            
            return {"success": True}

        except Exception as e:
            return {"success": False, "reason": "unknown_error", "error": f"Error checking cooldown: {e}"}

    def _is_within_working_hours(self, working_hours_config: dict) -> bool:
        """
        Config-Format:
        {
            "start": bool,
            "stop": bool,
            "hours": [
                {"days": [1,2,3,4,5], "start": "08:00", "end": "18:00"},
                {"days": [6], "start": "10:00", "end": "16:00"}
            ]
        }
        """
        try:
            now = datetime.now()
            current_day = now.weekday() + 1
            current_time = now.strftime("%H:%M")

            hours = working_hours_config.get("hours", [])

            for period in hours:
                if current_day in period["days"]:
                    start = period.get("start", "00:00")
                    end = period.get("end", "23:59")
                    if start <= current_time <= end:
                        return True

            return False

        except Exception as e:
            logger.error(f"Error occurred while checking working hours: {e}")
            return False
