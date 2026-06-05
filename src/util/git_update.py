import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

class GitUpdater:
    PROJECT_ROOT = Path(__file__).parent.parent.parent

    @staticmethod
    def update() -> dict:
        try:
            logger.info("Fetching latest changes from git...")
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=str(GitUpdater.PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"Git pull failed: {result.stderr}")
                return {"success": False, "message": result.stderr}

            logger.info(f"Git pull successful: \n{result.stdout}")
            return {"success": True, "message": "Git pull successful", "output": result.stdout}

        except subprocess.TimeoutExpired:
            logger.error("Git pull timed out")
            return {"success": False, "message": "Git pull timed out"}

        except Exception as e:
            logger.error(f"Error during git pull: {e}")
            return {"success": False, "message": str(e)}
