# src/manager/boot_manager.py
import logging
import subprocess
import time
from pathlib import Path
from src.db.mongo_client import get_mongo_client

logger = logging.getLogger(__name__)

class BootManager:
    SCRIPT_PATH = Path(__file__).parent / "scripts" 
    HOST_TYPE = "hardware"
    HOST_NAME = "claptp"
    POLL_INTERVAL = 2

    SCRIPT_MAPPING = {
        "start": "start_relay.py",
        "stop": "stop_relay.py",
    }

    def __init__(self):
        self.mongo_client = get_mongo_client()
        self.host_db = self.mongo_client.get_db("host")
        self.collection = self.host_db[self.HOST_TYPE]
        self.running = True
    
    def watch_for_boot_request(self):
        try:
            logger.info(f"Starting to watch for boot requests for host: {self.HOST_NAME}")

            while self.running:
                try:
                    host = self.collection.find_one({
                        "hostname": self.HOST_NAME,
                        "boot.request.requested": True
                    })

                    if host:
                        boot_data = host.get("boot", {})
                        request_data = boot_data.get("request", {})
                        action = request_data.get("action")
                        user_id = request_data.get("user_id")

                        if action:
                            logger.info(f"Received boot request: {action} for host: {self.HOST_NAME}")
                            result = self.execute_boot_action(action)
                            logger.info(f"Boot action result: {result}")

                            # Set requested flag to false
                            self.collection.update_one(
                                {"hostname": self.HOST_NAME},
                                {"$set": {"boot.request.requested": False}}
                            )
                        
                    time.sleep(self.POLL_INTERVAL)
                
                except Exception as e:
                    logger.error(f"Error processing boot request: {e}")
                    time.sleep(self.POLL_INTERVAL)

        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            raise

    def execute_boot_action(self, action: str, user_id: int = None) -> dict:
        try:
            script_name = self.SCRIPT_MAPPING.get(action)
            
            if not script_name:
                logger.error(f"Invalid boot action: {action}")
                return {"success": False, "message": f"Invalid action: {action}"}
            
            script_path = self.SCRIPT_PATH / script_name

            if not script_path.exists():
                logger.error(f"Script not found: {script_path}")
                return {"success": False, "message": f"Script not found: {script_path}"}
            
            logger.info(f"Executing script: {script_path} for action: {action}")

            result = subprocess.run(["python", str(script_path)], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                logger.info("Script executed successfully")
                return {"success": True, "output": result.stdout}
            else:
                logger.error(f"Script execution failed: {result.stderr}")
                return {"success": False, "message": result.stderr}
        
        except subprocess.TimeoutExpired:
            logger.error(f"Script execution timed out for action: {action}")
            return {"success": False, "message": "Script execution timed out"}
        
        except Exception as e:
            logger.error(f"Error executing boot action: {e}")
            return {"success": False, "message": str(e)}
    
    def stop(self):
        logger.info("Stopping BootManager")
        self.running = False
