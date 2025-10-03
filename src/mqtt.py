from src.config_manager import ConfigManager
import paho.mqtt.client as mqtt
import threading

class MqttManager:
    _cache = {}
    _client = None
    _lock = threading.Lock()
    _topic_prefix = "item/server/minecraft.tplr.eu/"

    @classmethod
    def connect(cls):
        if cls._client is not None:
            return
        config = ConfigManager.get_config('mqtt')
        cls._client = mqtt.Client()
        cls._client.username_pw_set(config['user'], config['password'])
        cls._client.on_message = cls._on_message
        cls._client.connect(config['broker'], config['port'])
        cls._client.subscribe(cls._topic_prefix + "#")
        thread = threading.Thread(target=cls._client.loop_forever, daemon=True)
        thread.start()

    @classmethod
    def _on_message(cls, client, userdata, msg):
        with cls._lock:
            cls._cache[msg.topic] = msg.payload.decode()

    @classmethod
    def read(cls, subject):
        cls.connect()
        full_topic = cls._topic_prefix + subject
        with cls._lock:
            return cls._cache.get(full_topic)
