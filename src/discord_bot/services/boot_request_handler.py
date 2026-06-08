import logging
from datetime import datetime
from src.util.db.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class BootRequestHandler:
    def handle_request(
            self,
            host_type= "hardware",
            hostname = "claptp",
            action = "start",
            skips = []
            ):
        try:
            # 1) check arguments
            valid_host_types = ["hardware", "vm"]
            if host_type not in valid_host_types:
                logger.warning("Invalid host_type requested:" + host_type)
                return {"success": False, "reason": "internal", "error": "invalid host_type"}

            host = DatabaseManager.get("host", host_type, {"hostname": hostname})
            if not host:
                logger.warning("Invalid hostname requested:" + hostname)
                return {"success": False, "reason": "internal", "error": "invalid hostname"}

            if action not in ["start", "stop", "restart", "kill"]:
                logger.warning("Invalid action requested:" + action)
                return {"success": False, "reason": "internal", "error": "invalid action"}

            # 2) Check host status
            if "host_status" not in skips:
                status_result = self.check_host_status(action, host_type, hostname)
                if not status_result["success"] or not status_result["pass"]:
                    return status_result

            # 3) Check restrictions
            if "boot_restrictions" not in skips:
                restriction_result = self.check_restrictions(action, host_type, hostname)
                if not restriction_result["success"]:
                    return restriction_result
                if not restriction_result["pass"]:
                    return restriction_result

            # 4) Check cooldown
            if "cooldown" not in skips:
                cooldown_result = self.check_cooldown(host_type, hostname)
                if not cooldown_result["success"] or not cooldown_result["pass"]:
                    return cooldown_result

            # 5) Enter boot request
            boot_request = {
                "requested": True,
                "action": action,
                "timestamp": datetime.now(),
            }
            DatabaseManager.set("host", host_type, {"hostname": hostname}, {"boot.request": boot_request})

            return {"success": True, "approved": True}
        
        except Exception as e:
            logger.error(f"Error handling boot request: {e}")
            return {"success": False, "reason": "internal", "error": str(e)}

    def check_host_status(self, action, host_type, hostname) -> dict:
        try:
            host = DatabaseManager.get("host", host_type, {"hostname": hostname}, "boot")
            host_status = host.get("status", "unknown")
        except Exception as e:
            logger.error(f"Failed to fetch host status: {e}")
            return {"success": False, "reason": str(e)}

        #TODO: Kill needs to be dependent on interaction.id rights
        if host_status == "starting":
            return {"success": True, "pass": False}
        elif action == "restart" and host_status != "on":
            return {"success": True, "pass": False}
        elif action == "start" and host_status == "on":
            return {"success": True, "pass": False}
        elif action == "stop" and host_status == "off":
            return {"success": True, "pass": False}

        return {"success": True, "pass": True}

    def check_restrictions(self, action, host_type, hostname):
        restrictions = DatabaseManager.get("host", host_type, {"hostname": hostname}, "boot.restrictions")

        if restrictions is None or restrictions == []:
            return {"success": True, "pass": True}
        
        restrictions = [r for r in restrictions if r.get("enabled", False)]

        for r in restrictions:
            # 1) ALWAYS_ALLOW
            if r["type"] == "ALWAYS_ALLOW":
                if r["config"].get(action, False):
                    return {"success": True, "pass": True, "reason": "ALWAYS_ALLOW"}
            # 2) SINGLE_SHOT
            if r["type"] == "SINGLE_SHOT":
                if r["config"].get(action, False):
                    r["config"][action] = False
                    DatabaseManager.set("host", host_type, {"hostname": hostname}, {"boot.restrictions": restrictions})
                    return {"success": True, "pass": True, "reason": "SINGLE_SHOT"}
            # 3) WORKING_HOURS
            if r["type"] == "WORKING_HOURS":
                if r["config"].get(action, False):
                    if self._is_within_working_hours(r["config"]):
                        return {"success": True, "pass": True, "reason": "WORKING_HOURS"}

        return {"success": True, "pass": False, "reason": "RESTRICTION"}

    def _is_within_working_hours(self, working_hours_config: dict) -> bool:
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

    def check_cooldown(self, host_type, hostname) -> dict:
        try:
            last_boot_time = DatabaseManager.get("host", host_type, {"hostname": hostname}, "boot.timestamp")
            boot_cooldown = DatabaseManager.get("host", host_type, {"hostname": hostname}, "boot.cooldown")
        except Exception as e:
            logger.error(f"Failed to fetch boot cooldown: {e}")
            return {"success": False, "reason":"internal", "error": str(e)}

        if not last_boot_time or not boot_cooldown: 
            return {"success": True, "pass": True}

        now = datetime.now()
        elapsed = (now - last_boot_time).total_seconds()

        if elapsed < boot_cooldown:
            remaining = boot_cooldown - int(elapsed)
            return {
                "success": True,
                "pass": False,
                "m": remaining // 60,
                "s": remaining % 60
            }

        return {"success": True, "pass": True}