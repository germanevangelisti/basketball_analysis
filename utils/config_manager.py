import yaml
import os
import logging

class ConfigManager:
    """
    Singleton class to manage configuration settings loaded from a YAML file.
    """
    _instance = None
    _config = None

    def __new__(cls, config_path="config.yaml"):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config(config_path)
        return cls._instance

    def _load_config(self, config_path):
        """
        Load configuration from the YAML file.
        """
        if not os.path.exists(config_path):
            logging.warning(f"Config file {config_path} not found. Using empty config.")
            self._config = {}
            return

        with open(config_path, 'r') as file:
            try:
                self._config = yaml.safe_load(file)
                logging.info(f"Configuration loaded from {config_path}")
            except yaml.YAMLError as e:
                logging.error(f"Error parsing config file: {e}")
                self._config = {}

    def get(self, key, default=None):
        """
        Retrieve a configuration value by key.
        """
        return self._config.get(key, default)

    @property
    def config(self):
        return self._config
