import os
import toml


if __name__ == "__main__":

    with open("../config.toml", "r") as c:
        user_config = toml.load(c)

    print("Saving enviroment variables to config.toml")

    user_config["Pocketsmith"]["pocketsmith_token"] = os.getenv("POCKETSMITH_TOKEN")
    user_config["Telegram"]["telegram_bot_token"] = os.getenv("TELEGRAM_TOKEN")
    user_config["Bot"]["private_ip"] = os.getenv("PRIVIP")
    user_config["Bot"]["domain"] = os.getenv("DOMAIN")

    with open("../config.toml", "w") as c:
        toml.dump(user_config, c)
