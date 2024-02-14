import toml
import telebot

with open("config.toml", "r") as c:
    user_config = toml.load(c)

    API_TOKEN = user_config["Telegram"]["telegram_bot_token"]
    WEBHOOK_HOST = user_config["Bot"]["domain"]
    WEBHOOK_PORT = user_config["Bot"]["port"]
    WEBHOOK_LISTEN = user_config["Bot"]["private_ip"]

WEBHOOK_SSL_CERT = (
    user_config["SSL"]["SSL_BASE_PATH"]
    + WEBHOOK_HOST
    + "/"
    + user_config["SSL"]["WEBHOOK_SSL_CERT"]
)
WEBHOOK_SSL_PRIV = (
    user_config["SSL"]["SSL_BASE_PATH"]
    + WEBHOOK_HOST
    + "/"
    + user_config["SSL"]["WEBHOOK_SSL_PRIV"]
)

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (API_TOKEN)

bot = telebot.TeleBot(API_TOKEN, threaded=False)
