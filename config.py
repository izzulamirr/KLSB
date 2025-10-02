class BaseConfig:
    SECRET_KEY = "change-me"  # In production load from env var

class DevConfig(BaseConfig):
    DEBUG = True
