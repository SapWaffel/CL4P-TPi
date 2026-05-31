import logging
from datetime import datetime
from src.models import BootRequest, BootRequestStatus
from src.discord_bot.services.restriction_service import RestrictionService

logger = logging.getLogger(__name__)

class BootRequestHandler:

    def __init__(self):
        self.restriction_service = RestrictionService()

    def handle_request(self, user_id: int, action: str) -> dict:
        try:
            result = self.restriction_service.get_all_restrictions()
            if not result["success"]:
                return {"success": False, "error": "Restriction not available"}
            
            restrictions = result["restrictions"]

            # 1) ALWAYS_ALLOW
            for restriction in restrictions:
                if restriction["type"] == "ALWAYS_ALLOW" and restriction["enabled"]:
                    if restriction["config"].get(action, False):
                        logger.info(f"{action.capitalize()} request from user {user_id} allowed by ALWAYS_ALLOW restriction.")
                        return {"success": True, "status": BootRequestStatus.APPROVED.value, "reason": "ALWAYS_ALLOW restriction"}
                    
            # 2) SINGLE_SHOT
            for restriction in restrictions:
                if restriction["type"] == "SINGLE_SHOT" and restriction["enabled"]:
                    if restriction["config"].get(action, False):
                        logger.info(f"{action.capitalize()} request from user {user_id} allowed by SINGLE_SHOT restriction.")
                        # disable SINGLE_SHOT restriction after use
                        self.restriction_service.collection.update_one(
                            {"_id": restriction["_id"]},
                            {"$set": {"enabled": False}}
                        )
                        return {"success": True, "status": BootRequestStatus.APPROVED.value, "reason": "SINGLE_SHOT restriction"}
            
            # 3) WORKING_HOURS
            for restriction in restrictions:
                if restriction["type"] == "WORKING_HOURS" and restriction["enabled"]:
                    if restriction["config"].get(action, False):
                        if self._is_within_working_hours(restriction["config"]):
                            logger.info(f"{action.capitalize()} request from user {user_id} allowed by WORKING_HOURS restriction.")
                            return {"success": True, "status": BootRequestStatus.APPROVED.value, "reason": "WORKING_HOURS restriction"}
        
            logger.warning(f"{action.capitalize()} request from user {user_id} rejected - no applicable restrictions allowed it.")
            return {"success": True, "status": BootRequestStatus.REJECTED.value, "reason": "No applicable restrictions allowed the request"}
        
        except Exception as e:
            logger.error(f"Error occurred while handling boot request from user {user_id}: {e}")
            return {"success": False, "error": f"{e}"}
        
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