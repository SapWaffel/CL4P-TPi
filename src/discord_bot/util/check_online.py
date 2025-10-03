from src.mqtt import MqttManager

def check_status():
    status = MqttManager.read("status")
    return status