# This script pulls all the existing data from the Pocketsmith DB and creates the lists.json file that is going to be used by the bot.
import requests
import json
import toml


def get_payees() -> list:
    i = 1
    unique_payees = []
    while True:
        ans = requests.get(
            Pocketsmith_BASE_URL
            + "users/%s/transactions?page=%s" % (user_config["Pocketsmith"]["user"], i),
            headers=headers,
        )
        if ans.status_code == 200:
            ans_json = json.loads(ans.content)
            for tx in ans_json:
                if tx["needs_review"] == False:
                    unique_payees.append(tx["payee"])
        if ans.status_code == 400:
            unique_payees = list(set(unique_payees))
            break
        i += 1
    return unique_payees


def get_accounts() -> list:
    accounts = []
    ans = requests.get(
        Pocketsmith_BASE_URL
        + "users/%s/transaction_accounts" % user_config["Pocketsmith"]["user"],
        headers=headers,
    )
    ans_json = json.loads(ans.content)
    for account in ans_json:
        accounts.append(
            {
                "name": account["name"],
                "id": account["id"],
                "thumbnail": account["institution"]["title"] + ".png",
            },
        )
    return accounts


def get_categories() -> list:
    categories = []
    ans = requests.get(
        Pocketsmith_BASE_URL
        + "users/%s/categories" % user_config["Pocketsmith"]["user"],
        headers=headers,
    )
    ans_json = json.loads(ans.content)
    for category in ans_json:
        categories.append(
            {
                "name": category["title"],
                "id": category["id"],
                "tx": category["is_transfer"],
            }
        )
    return categories


def get_labels() -> list:
    labels = []
    ans = requests.get(
        Pocketsmith_BASE_URL + "users/%s/labels" % user_config["Pocketsmith"]["user"],
        headers=headers,
    )
    labels = json.loads(ans.content)
    return labels


if __name__ == "__main__":
    with open("config.toml", "r") as c:
        user_config = toml.load(c)

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-Developer-Key": user_config["Pocketsmith"]["pocketsmith_token"],
    }

    Pocketsmith_BASE_URL = user_config["Pocketsmith"]["base_url"]

    json_file = {
        "payees": [],
        "categories": [],
        "accounts": [],
        "labels": [],
        "payment_methods": [],
        "taxes": [],
    }

    print("Getting payees")
    json_file["payees"] = get_payees()

    print("Getting categories")
    json_file["categories"] = get_categories()

    print("Getting accounts")
    json_file["accounts"] = get_accounts()

    print("Getting labels")
    json_file["labels"] = get_labels()

    print("Saving lists to file")
    with open("./lists.json", "w", encoding="utf-8") as lists:
        json.dump(json_file, lists, ensure_ascii=False)
