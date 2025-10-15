# src/discord_bot/util/GitUpdater.py
import json
import requests
import sys
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType
from src.config_manager import ConfigManager

def get_git_version():
    url = "https://raw.githubusercontent.com/SapWaffel/CL4P-TPi/main/config/_global.json"
    response = requests.get(url)
    response.raise_for_status()
    return json.loads(response.text)["version"]

def download_and_replace_files():
    base_url = "https://raw.githubusercontent.com/SapWaffel/CL4P-TPi/main/",
    files_to_update = [
        "src/discord_bot/bot.py"
    ]
    
    for file in files_to_update:
        file_url = base_url + file
        response = requests.get(file_url)
        response.raise_for_status()
        with open(file, "wb") as f:
            f.write(response.content)

def parse_version(version_str):
    version_str = version_str.replace("SNAPSHOT-", "")
    return tuple(int(part) for part in version_str.split("."))

def check_for_updates():
    local = ConfigManager.get_config('_global')['version']
    remote = get_git_version()

    # remove "SNAPSHOT-" prefix if exists
    local_tuple = parse_version(local)
    remote_tuple = parse_version(remote)

    if remote_tuple > local_tuple:
        RelevanceLogger.write_log_entry(f"Update available: {local} -> {remote}. Downloading...", "SYSTEM", LogType.INFO)
        download_and_replace_files()
        RelevanceLogger.write_log_entry("Update downloaded. Restarting to apply changes...", "SYSTEM", LogType.INFO)
        sys.exit(0)

check_for_updates()