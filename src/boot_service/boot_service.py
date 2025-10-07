import RPi.GPIO as GPIO
import time
import json
from src.mqtt import MqttManager
from src.config_manager import ConfigManager

def write_json(data, file="boot_info.json"):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def check_boot_cooldown(difference_seconds=10, return_remaining=False):
    boot_time = MqttManager.read("boot_time")
    boot_time = float(boot_time) if boot_time is not None else 0
    current_time = time.time()
    
    if return_remaining:
        remaining = difference_seconds - (current_time - boot_time)
        return {"can_boot": remaining <= 0, "remaining": max(0, remaining)}
    else:
        return (current_time - boot_time) >= difference_seconds


def send_boot_signal():
    # Set GPIO-Modus (BCM)
    GPIO.setmode(GPIO.BCM)
    RELAY_PINS = [7, 3, 22, 25]

    for pin in RELAY_PINS:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
		
    # Relais einschalten
    GPIO.output(RELAY_PINS[2], GPIO.HIGH)
    time.sleep(0.1)  
    GPIO.output(RELAY_PINS[2], GPIO.LOW)

    # Aufräumen
    GPIO.cleanup()
    return {"success": True}

def boot(cooldown_seconds=10):
    check_boot = check_boot_cooldown(cooldown_seconds, return_remaining=True)
    if not check_boot["can_boot"]:
        return {"success": False, "error": f"{ConfigManager.get_config('strings')['response']['request']['deny']['cooldown'].replace('{m}', str(int(check_boot['remaining'] // 60))).replace('{s}', str(int(check_boot['remaining'] % 60)))}"}

    try:
        send_boot_signal()
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {"success": True}

def reboot():
    if not check_boot_cooldown():
        return {"success": False, "error": f"{ConfigManager.get_config('strings')['response']['request']['deny']['cooldown']}"}
    
    try:
        send_boot_signal()
    except Exception as e:
        return {"success": False, "error": str(e)}

    time.sleep(5)

    try:
        send_boot_signal()
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {"success": True}