import toml
import telebot
import time
import os

if __name__ == "__main__":

    with open("../config.toml", "r") as c:
        user_config = toml.load(c)

    print("Saving enviroment variables to config.toml")

    user_config["Pocketsmith"]["pocketsmith_token"] = os.getenv("POCKETSMITH_TOKEN")
    user_config["Pocketsmith"]["user"] = os.getenv("PS_USER")
    API_TOKEN = user_config["Telegram"]["telegram_bot_token"] = os.getenv(
        "TELEGRAM_TOKEN"
    )
    user_config["Telegram"]["authorized_users"] = [int(os.getenv("TG_USER"))]
    WEBHOOK_LISTEN = user_config["Bot"]["private_ip"] = os.getenv("PRIVIP")
    WEBHOOK_HOST = user_config["Bot"]["domain"] = os.getenv("DOMAIN")
    user_config["Pocketsmith"]["user"] = os.getenv("PS_USER")
    WEBHOOK_PORT = user_config["Bot"]["port"]

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

    with open("../config.toml", "w") as c:
        toml.dump(user_config, c)

    bot.remove_webhook()

    time.sleep(0.1)

    # Set webhook
    bot.set_webhook(
        url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
        drop_pending_updates=True,
    )
