# src/manager/boot_manager.py
import logging
import subprocess
import time
import os
import sys
from pathlib import Path
from datetime import datetime
from src.util.db.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

ACTION_RESULT_STATUS = {
    "start": "on",
    "restart": "on",
    "stop": "off",
    "kill": "off"
}

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
                    self._process_pending_requests()
                except Exception as e:
                    logger.error(f"Error processing boot requests: {e}", exc_info=True)

                time.sleep(self.POLL_INTERVAL)

        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            raise

    def _process_pending_requests(self):
        for host_type, collection in self.collections.items():
            for host in collection.find({"boot.request.requested": True}):
                self._handle_boot_request(host_type, collection, host)

    def _handle_boot_request(self, host_type: str, collection, host: str):
        hostname = host.get("hostname")
        boot = host.get("boot", {})
        boot_request = boot.get("request", {})
        boot_type = boot.get("type")
        action = boot_request.get("action")

        if not hostname:
            logger.error(f"Skipping a boot request in '{host_type}': document has no 'hostname' field")
            return

        if not action:
            logger.error(f"Skipping boot request for {hostname}: request is missing 'action' field.")
            self._finish_request(collection, hostname, success=False, error="Keine Aktion in der Anfrage angegeben")
            return

        if not boot_type:
            logger.error(f"Skipping boot request for {hostname}: boot type is not specified.")
            self._finish_request(collection, hostname, success=False, error="Kein 'boot.type' für diesen Host konfiguriert")
            return

        collection.update_one(
            {"hostname": hostname},
            {"$set": {"boot.request.state": "running", "boot.request.started_at": datetime.now()}}
        )

        result = self.execute_boot_action(host_type, hostname, boot_type, action)

        if result.get("success"):
            self._finish_request(collection, hostname, success=True, new_status=ACTION_RESULT_STATUS.get(action))
            logger.info(f"Boot action '{action}' for {hostname} completed successfully")
        else:
            error = result.get("error", {}).get("e", "Unknown error")
            logger.error(f"Boot action '{action}' failed for {hostname}: {error}")
            self._finish_request(collection, hostname, success=False, error=error)

    def _finish_request(self, collection, hostname: str, success: bool, new_status: str = None, error: str = None):

        # always update boot request
        update = {
            "boot.request.requested": False,
            "boot.request.state": "success" if success else "failed",
            "boot.request.finished_at": datetime.now(),
            "boot.request.error": error
        }

        # save boot time
        if success:
            update["boot.timestamp"] = datetime.now()

        # update boot status
        if new_status:
            update["boot.status"] = new_status

        update_result = collection.update_one({"hostname": hostname}, {"$set": update})
        logger.debug(
            f"Request finished for {hostname} (success={success})"
            f"{update_result.modified_count} document(s) updated"
        )

    def execute_boot_action(self, host_type: str, hostname: str, boot_type: str, action: str) -> dict:

        # get script file
        script_file = self.SCRIPT_PATH / host_type / boot_type / f"{action}.sh"
        if not script_file.exists():
            logger.error(f"Boot script not found: {script_file}")
            return {"success": False, "error": {"type":"unknown", "e": "Boot-Skript nicht gefunden"}}

        # run script
        try:
            env = os.environ.copy()
            project_root = Path(__file__).parent.parent.parent
            env["PYTHONPATH"] = str(project_root)

            logger.debug(f"Starting subprocess: python3 {script_file}")

            result = subprocess.run(
                [sys.executable, str(script_file)],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=str(project_root)
            )

            # process result
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                logger.error(f"Boot script failed: {result.stderr}")
                return {"success": False, "error": {"type":"unknown", "e": result.stderr or "Skript beendet mit Fehlercode"}}

        except subprocess.TimeoutExpired:
            logger.error(f"Boot script timed out: {script_file}")
            return {"success": False, "error": {"type":"unknown", "e": "Skript-Timeout"}}

        except Exception as e:
            logger.error(f"Error executing boot script: {e}", exc_info=True)
            return {"success": False, "error": {"type":"unknown", "e": str(e)}}

    def stop(self):
        logger.info("Stopping BootManager...")
        self.running = False