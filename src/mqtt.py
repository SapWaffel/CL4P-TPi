from src.config_manager import ConfigManager
import paho.mqtt.client as mqtt
import threading, time, ssl
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

class MqttManager:
    _cache = {}
    _client = None
    _lock = threading.Lock()
    _topic_prefix = "item/server/minecraft.tplr.eu/"

    @classmethod
    def connect(cls):
        if cls._client is not None:
            return
        config = ConfigManager.get_config(module='mqtt')
        RelevanceLogger.write_log_entry(config, "SYSTEM", LogType.INFO)
        cls._client = mqtt.Client()
        cls.context = ssl.create_default_context()
        cls.context.check_hostname = False
        cls.context.verify_mode = ssl.CERT_NONE
        cls._client.tls_set_context(cls.context)  # <--- Das fehlt!
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
        time.sleep(0.1)
        full_topic = cls._topic_prefix + subject
        print(full_topic)
        with cls._lock:
            return cls._cache.get(full_topic)

