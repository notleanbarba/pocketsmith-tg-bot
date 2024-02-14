import os
import toml
import telebot
import time
from init import API_TOKEN, WEBHOOK_URL_BASE, WEBHOOK_URL_PATH

if __name__ == "__main__":

    with open("../config.toml", "r") as c:
        user_config = toml.load(c)

    print("Saving enviroment variables to config.toml")

    user_config["Pocketsmith"]["pocketsmith_token"] = os.getenv("POCKETSMITH_TOKEN")
    user_config["Pocketsmith"]["user"] = os.getenv("PS_USER")
    user_config["Telegram"]["telegram_bot_token"] = os.getenv("TELEGRAM_TOKEN")
    user_config["Telegram"]["authorized_users"] = [int(os.getenv("TG_USER"))]
    user_config["Bot"]["private_ip"] = os.getenv("PRIVIP")
    user_config["Bot"]["domain"] = os.getenv("DOMAIN")
    user_config["Pocketsmith"]["user"] = os.getenv("PS_USER")

    with open("../config.toml", "w") as c:
        toml.dump(user_config, c)

    bot = telebot.TeleBot(user_config["Telegram"]["telegram_bot_token"], threaded=False)

    bot.remove_webhook()

    time.sleep(0.1)

    # Set webhook
    bot.set_webhook(
        url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
        drop_pending_updates=True,
    )
