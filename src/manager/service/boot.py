import RPi.GPIO as GPIO
import time

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


def boot():
    try:
        send_boot_signal()
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {"success": True}


def reboot():
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
