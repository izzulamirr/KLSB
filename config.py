# config.py
import os
from urllib.parse import quote_plus

class BaseConfig:

    ADMIN_USER = os.environ.get("ADMIN_USER", "klsbadmin")
    ADMIN_PASS = os.environ.get("ADMIN_PASS", "klsb123")

    SECRET_KEY = "4d453d84e5c971b955366b277637c340ed34d10b9b05850bd3e6dc24de04980d"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # === MySQL (your local DB) ===
    DB_USER = "root"                      # Default XAMPP/Laragon/MAMP user
    DB_PASS = ""                          # Empty for local development
    DB_NAME = "klsb_test"                 # Your database from phpMyAdmin
    DB_HOST = "localhost"
    DB_PORT = "3306"

    user_q = quote_plus(DB_USER)
    pass_q = quote_plus(DB_PASS) if DB_PASS else ""
    db_q   = quote_plus(DB_NAME)

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqlconnector://{user_q}:{pass_q}@{DB_HOST}:{DB_PORT}/{db_q}?charset=utf8mb4"
    )

class DevConfig(BaseConfig):
    DEBUG = True

class ProdConfig(BaseConfig):
    DEBUG = False