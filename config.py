import os

class BaseConfig:
    """Base configuration shared by all environments."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "4d453d84e5c971b955366b277637c340ed34d10b9b05850bd3e6dc24de04980d")

    # SQLAlchemy Database configuration
    DB_USER = os.environ.get("DB_USER")
    DB_PASS = os.environ.get("DB_PASS")
    DB_NAME = os.environ.get("DB_NAME")
    DB_HOST = os.environ.get("DB_HOST", "localhost")

    if DB_USER and DB_PASS and DB_NAME:
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
    else:
        SQLALCHEMY_DATABASE_URI = None

    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevConfig(BaseConfig):
    DEBUG = True


class ProdConfig(BaseConfig):
    DEBUG = False
