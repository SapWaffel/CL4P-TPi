# src/manager/boot_manager.py
import logging
import subprocess
import time
import os
from pathlib import Path
from src.util.db.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class BootManager:
    SCRIPT_PATH = Path(__file__).parent / "scripts" 
    POLL_INTERVAL = 2

    def __init__(self):
        manager = DatabaseManager()
        self.host_db = manager.mongo_client.get_db("host")
        self.collections = {
            "hardware": self.host_db["hardware"],
            "vm": self.host_db["vm"]
        }
        self.running = True
    
    def watch_for_boot_request(self):
        try:
            while self.running:
                try:
                    requested_hosts = []

                    for host_type, collection in self.collections.items():
                        hosts = collection.find({"boot.request.requested": True})
                        for host in hosts:
                            host["_host_type"] = host_type
                            requested_hosts.append(host)

                    for host in requested_hosts:
                        host_type = host.get("_host_type")
                        hostname = host.get("hostname")
                        boot_request = host.get("boot", {}).get("request", {})
                        boot_type = host.get("boot",{}).get("type", {})
                        boot_action = boot_request.get("action")

                        if boot_action and host_type and hostname and boot_type:
                            logger.info(f"Executing boot request: {boot_action} via {boot_type} for: {host_type}/{hostname}")
                            result = self.execute_boot_action(host_type, hostname, boot_type, boot_action)
                            logger.info(f"Boot action result: {result}")

                            # Set requested flag to false
                            collection = self.collections[host_type]
                            update_result = collection.update_one(
                                {"hostname": hostname},
                                {"$set": {"boot.request.requested": False}}
                            )
                            logger.debug(f"Request flag cleared for {hostname}: : {update_result.modified_count} document(s) updated")
                        
                    time.sleep(self.POLL_INTERVAL)
                
                except Exception as e:
                    logger.error(f"Error processing boot request: {e}", exc_info=True)
                    time.sleep(self.POLL_INTERVAL)

        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            raise

    def execute_boot_action(self, host_type: str, hostname: str, boot_type: str, action: str) -> dict:
        script_file = self.SCRIPT_PATH / host_type / boot_type / f"{action}.py"

        if not script_file.exists():
            logger.error(f"Boot script not found: {script_file}")
            return {"success": False, "error": {"type": "unknown", "e": "Boot-Skript nicht gefunden"}}

        try:
            env = os.environ.copy()
            project_root = Path(__file__).parent.parent.parent
            env["PYTHONPATH"] = str(project_root)

            logger.debug(f"Starting subprocess: python3 {script_file}")

            result = subprocess.run(
                ["python3", str(script_file)],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=str(project_root),
            )

            if result.returncode == 0:
                if action == "start":
                    DatabaseManager.set("host", host_type, {"hostname": hostname}, {"boot.status": "starting"})

                return {"success": True, "output": result.stdout}
            else:
                logger.error(f"Boot script failed: {result.stderr}")
                return {"success": False, "error": {"type": "unknown", "e": result.stderr}}

        except subprocess.TimeoutExpired:
            logger.error(f"Boot script timeout: {script_file}")
            return {"success": False, "error": {"type": "unknown", "e": "Script timeout"}}

        except Exception as e:
            logger.error(f"Error executing boot action: {e}", exc_info=True)
            return {"success": False, "error": {"type": "unknown", "e": str(e)}}
        
    def stop(self):
        logger.info("Stopping BootManager")
        self.running = False
