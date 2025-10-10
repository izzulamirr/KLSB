# config.py
from urllib.parse import quote_plus

class BaseConfig:
    SECRET_KEY = "4d453d84e5c971b955366b277637c340ed34d10b9b05850bd3e6dc24de04980d"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # === MySQL (your cPanel DB) ===
    DB_USER = "kemunca_akmalhaziq"
    DB_PASS = "akmal@kl$8kl$8"             # contains @ and $, so we URL-encode below
    DB_NAME = "kemunca_website_Akmal"
    DB_HOST = "localhost"
    DB_PORT = "3306"

    user_q = quote_plus(DB_USER)
    pass_q = quote_plus(DB_PASS)
    db_q   = quote_plus(DB_NAME)

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqlconnector://{user_q}:{pass_q}@{DB_HOST}:{DB_PORT}/{db_q}?charset=utf8mb4"
    )

class DevConfig(BaseConfig):
    DEBUG = True

class ProdConfig(BaseConfig):
    DEBUG = False
