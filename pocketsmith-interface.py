import requests
import json
import toml


with open("config.toml", "r") as c:
    user_config = toml.load(c)

eth_balance = user_config["Pocketsmith"]["eth_balance"]
user = user_config["Pocketsmith"]["user"]

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "X-Developer-Key": user_config["Pocketsmith"]["pocketsmith_token"],
}
Pocketsmith_BASE_URL = user_config["Pocketsmith"]["base_url"]

lists = json.load(open("./lists.json", "r", encoding="utf-8"))
accounts_list = lists["accounts"]
categories_list = lists["categories"]
labels_list = lists["labels"]
payees_list = lists["payees"]
payment_method_list = lists["payment_methods"]
tax_list = lists["taxes"]


def addPayee(newPayee):
    tmp = set(payees_list)
    tmp.add(newPayee)
    lists["payees"] = list(tmp)
    with open("lists.json", "w", encoding="utf-8") as JSONList:
        json.dump(lists, JSONList, ensure_ascii=False)


# TODO: Rutinary check and deletion of unused payees


def deletePayee(oldPayee):
    tmp = set(payees_list)
    if oldPayee in tmp:
        tmp.remove(oldPayee)
    lists["payees"] = list(tmp)
    with open("./lists.json", "w", encoding="utf-8") as JSONList:
        json.dump(lists, JSONList, ensure_ascii=False)


def addLabel(newLabel):
    tmp = set(labels_list)
    tmp.add(newLabel)
    lists["labels"] = list(tmp)
    with open("./lists.json", "w", encoding="utf-8") as JSONList:
        json.dump(lists, JSONList, ensure_ascii=False)


def getNameByID(id, type):
    if type == "account":
        for elem in accounts_list:
            if elem["id"] == id:
                return elem["name"]
    if type == "category":
        for elem in categories_list:
            if elem["id"] == id:
                return elem["name"]


def getIDByName(name, type) -> int:
    if type == "account":
        for elem in accounts_list:
            if elem["name"] == name:
                return int(elem["id"])
    if type == "category":
        for elem in categories_list:
            if elem["name"] == name:
                return int(elem["id"])
    return 0


def uploadTxToPocketsmith(
    date, payee, amount, category_id, note, labels, type, account, file=[]
):
    payload_tx = {
        "date": date,
        "payee": payee,
        "amount": amount,
        "category_id": category_id,
        "note": note,
        "labels": labels,
        "is_transfer": type,
    }
    response_tx = requests.post(
        f"{Pocketsmith_BASE_URL}transaction_accounts/{account}/transactions",
        json=payload_tx,
        headers=headers,
    )
    response = response_tx
    response_tx = json.loads(response_tx.text)
    if file:
        for f in file:
            payload_file = {
                "file_name": date + "_" + payee + "-" + getNameByID(account, "account"),
                "file_data": f,
            }
            response_file = requests.post(
                f"{Pocketsmith_BASE_URL}users/{user}/attachments",
                json=payload_file,
                headers=headers,
            )
            response_file = json.loads(response_file.text)
            response = requests.post(
                Pocketsmith_BASE_URL
                + "transactions/%s/attachments" % response_tx["id"],
                json={"attachment_id": response_file["id"]},
                headers=headers,
            )
    return response


def createNote(
    category_id=0,
    installments=1,
    third_party="",
    related_account=0,
    payment_method="",
    reference="",
    tax="",
    pair_exchanged=["", ""],
    income=False,
    amount=float(),
    date="",
) -> list[str]:
    # Gastos en ciertas categorias
    match category_id:
        # 1) Internal Transfers OK
        case 14986880:
            if income:
                return ["De %s" % getNameByID(related_account, "account")]
            return ["A %s" % getNameByID(related_account, "account")]

        # 2) Payments and Credits OK
        case 14978204:
            if income:
                return [
                    "Credito por %s - %s %s"
                    % (
                        payment_method,
                        getNameByID(related_account, "account"),
                        reference,
                    )
                ]
            return ["Pago %s %s" % (getNameByID(related_account, "account"), reference)]

        # 7) Tax OK
        case 14976197:
            return ["Federal " + tax + " " + reference]
        case 14976200:
            return ["Estatal/Provincial " + tax + " " + reference]

        # 8) Crypto OK
        case 14977142:
            if income:
                return [
                    f"%s, %s - %s/%s %s %s"
                    % (
                        getNameByID(related_account, "account"),
                        third_party,
                        pair_exchanged[0],
                        pair_exchanged[1],
                        amount,
                        pair_exchanged[0],
                    )
                ]
            return [
                "%s, %s - %s/%s %s %s"
                % (
                    getNameByID(related_account, "account"),
                    third_party,
                    pair_exchanged[0],
                    pair_exchanged[1],
                    amount,
                    pair_exchanged[1],
                )
            ]

    # 4) Gastos en cuotas OK
    if installments > 1:
        tmp = []
        for i in range(1, installments + 1):
            str = "%s - Cuota %s/%s" % (reference, i, installments)
            tmp.append(str)
        return tmp

    # 3) y 9) Pago o credito de terceras personas OK
    if third_party:
        if income:
            return [
                "Pago a cuenta de %s - %s"
                % (third_party, getNameByID(related_account, "account"))
            ]
        return [
            "Credito por consumo en %s - %s %s"
            % (third_party, date, getNameByID(related_account, "account"))
        ]
    return [reference]
