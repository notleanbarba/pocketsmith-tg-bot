from init import WEBHOOK_URL_BASE, WEBHOOK_URL_PATH, bot, AUTHORIZED_USERS
import pocketsmith_interface 
from telegram_bot_calendar import WMonthTelegramCalendar, LSTEP
from datetime import date, datetime
from telebot.types import Message, InlineQueryResultArticle, InputTextMessageContent
from telebot.util import quick_markup
import re


tmp_files = []

c_1, s_1 = WMonthTelegramCalendar(
    calendar_id=0,
    additional_buttons=[
        {
            "text": f"Hoy {str(date.today().strftime('%d-%m-%Y'))}",
            "callback_data": "cbcal_0select_today",
        }
    ],
).build()

c_2, s_2 = WMonthTelegramCalendar(
    calendar_id=1,
    additional_buttons=[
        {
            "text": f"Hoy {str(date.today().strftime('%d-%m-%Y'))}",
            "callback_data": "cbcal_1select_today",
        }
    ],
).build()


def checkUserPermits(message: Message):
    if message.chat.id not in AUTHORIZED_USERS:
        bot.send_message(chat_id=message.chat.id, text="Usuario no autorizado")
        raise Exception("Usuario no autorizado")
    return True


@bot.message_handler(commands=["upload_tx"])
def upload_tx(message):
    checkUserPermits(message)
    global new_tx, files_ans_id, current_step, m_id
    files_ans_id = 0
    current_step = [0, 0, 0, 0, 0, 0]
    m_id = message.chat.id
    new_tx = {
        "date": "",
        "account": 0,
        "payee": "",
        "category": 0,
        "amount": 0.00,
        "txtype": False,
        "label": [],
        "installments": 1,
        "third_party": "",
        "tx_date": "",
        "related_account": 0,
        "payment_method": "",
        "tax": "",
        "reference": "",
        "pair_exchanged": ["", ""],
        "note": [],
        "file": [],
        "income": False,
    }
    bot.reply_to(
        message,
        text=STEP[current_step[0]][0][0],
        reply_markup=STEP[current_step[0]][0][1],
    )
    current_step[0] += 1


@bot.message_handler(commands=["done_files"])
def finish_files(message):
    bot.clear_step_handler(message)
    bot.reply_to(message, f"Comprobantes cargados.")
    process_tx()


# STAGE 0: DATE
@bot.callback_query_handler(func=WMonthTelegramCalendar.func(calendar_id=0))
def cal(c):
    message = c.message
    if c.data == "cbcal_0select_today":
        result = date.today()
    else:
        result, key, step = WMonthTelegramCalendar().process(c.data)  # type: ignore
    if not result and key:  # type: ignore
        bot.edit_message_text(
            f"Seleccione {LSTEP[step]}",  # type: ignore
            m_id,
            message.message_id,
            reply_markup=key,  # type: ignore
        )
    elif result:
        new_tx["date"] = str(result)
    bot.edit_message_text(
        "La fecha seleccionada es %s"
        % datetime.strptime(new_tx["date"], "%Y-%m-%d").strftime("%d-%m-%y"),
        m_id,
        message.message_id,
    )
    next_step()


# STAGE 1: ACCOUNT
def process_account(message):
    if message.text in pocketsmith_interface.acc:
        new_tx["account"] = int(
            pocketsmith_interface.getIDByName(message.text, "account")
        )
        bot.reply_to(message, f"Cuenta {message.text} aceptada.")
        return next_step()
    ans = bot.reply_to(
        message,
        f"La cuenta {message.text} no se encuentra en la lista de cuentas. Por favor, intente nuevamente con una cuenta aceptable.",
    )
    bot.register_next_step_handler(ans, process_account)


# STAGE 2: PAYEE
def process_payee_1(message):
    if message.text == "*&Nuevo Pagador&*":
        ans = bot.reply_to(message, "¿Como se llama el nuevo pagador?")
        return bot.register_next_step_handler(ans, process_payee_2)
    if message.text not in pocketsmith_interface.payees_list:
        ans = bot.reply_to(
            message,
            "El pagador no se encuentra en la lista disponible. Utilice la lista validada o agregue uno nuevo.",
        )
        return bot.register_next_step_handler(ans, process_payee_1)
    new_tx["payee"] = message.text
    bot.reply_to(message, f"Pagador {message.text} aceptado")
    next_step()


def add_payee(message, param="payee"):
    pocketsmith_interface.addPayee(message.text)
    new_tx[param] = message.text
    bot.reply_to(message, f"Nuevo pagador {message.text} agregado y aceptado.")


def process_payee_2(message):
    if message.text.lower() not in [
        x.lower() for x in pocketsmith_interface.payees_list
    ]:
        add_payee(message)
        return next_step()
    process_payee_1(message)


# STAGE 3: CATEGORY
def process_category(message):
    cat = []
    for p in pocketsmith_interface.categories_list:
        cat.append(p["name"])
    if message.text in cat:
        new_tx["category"] = pocketsmith_interface.getIDByName(message.text, "category")
        bot.reply_to(message, f"Categoria {message.text} aceptada.")
        return next_step()
    ans = bot.reply_to(
        message,
        f"Categoria {message.text} no se encuentra en la lista de categorias. Por favor, intente nuevamente con una categoria aceptable.",
    )
    bot.register_next_step_handler(ans, process_category)


# STAGE 4: AMOUNT
def process_amount(message):
    m = re.search("[+]", message.text)
    try:
        if m:
            new_tx["income"] = True
            new_tx["amount"] = round(float(message.text[: m.span()[0]]), 2)
        else:
            new_tx["amount"] = round(float(message.text), 2)
        bot.reply_to(
            message,
            (
                "Importe +%s aceptado." % new_tx["amount"]
                if new_tx["income"]
                else "Importe -%s aceptado." % new_tx["amount"]
            ),
        )
        next_step()
    except Exception as e:
        ans = bot.reply_to(
            message,
            "El valor ingresado no es numerico. Intente nuevamente. Recuerde que el valor ingresado debe seguir el siguiente formato XXX.XX",
        )
        bot.register_next_step_handler(ans, process_amount)


# STAGE 5: LABEL
def process_label(message):
    if (
        message.text in pocketsmith_interface.labels_list
        and message.text not in new_tx["label"]
    ):
        new_tx["label"].append(message.text)
        bot.reply_to(
            message,
            f"Etiqueta {message.text} agregada. ¿Desea agregar una nueva etiqueta?",
            reply_markup=quick_markup(
                {
                    "Si": {"callback_data": "add_new_label"},
                    "No": {"callback_data": "no_new_label"},
                },
                row_width=2,
            ),
        )


@bot.callback_query_handler(func=lambda c: c.data == "cancel_labels")
def cancel_labels(c):
    bot.clear_step_handler(c.message)
    ans = bot.send_message(m_id, "Ninguna etiqueta fue agregada")
    process_special_categories(ans)


@bot.callback_query_handler(func=lambda c: c.data == "add_new_label")
def add_new_label(c):
    ans = bot.send_message(
        m_id,
        "¿Que etiqueta quiere eligir?",
        reply_markup=quick_markup(
            {
                "Buscar entre datos validados": {
                    "switch_inline_query_current_chat": "/label "
                }
            },
            row_width=1,
        ),
    )
    bot.register_next_step_handler(ans, process_label)


@bot.callback_query_handler(func=lambda c: c.data == "no_new_label")
def no_new_label(c):
    bot.send_message(m_id, "Etiquetas aceptadas.")
    process_special_categories(c.message)


# STAGE 6: SPECIAL CATEGORY
def process_special_categories(message):
    match new_tx["category"]:
        case 14986880:
            return next_step(step_routine=1)
        case 14978204:
            return next_step(step_routine=2)
        case 14976197 | 14976200:
            return next_step(step_routine=3)
        case 14977142:
            return ask_file(message)
    bot.send_message(
        m_id,
        "Seleccione una opción adicional de la siguiente lista.",
        reply_markup=quick_markup(
            {
                "Transacción en cuotas": {"callback_data": "installments"},
                "Transacción de tercero": {"callback_data": "third_party"},
                "Ninguna": {"callback_data": "none"},
            },
            row_width=2,
        ),
    )


# STAGE 6A: Internal Transfers
def process_related_account(message):
    if message.text in pocketsmith_interface.acc:
        new_tx["related_account"] = pocketsmith_interface.getIDByName(
            message.text, "account"
        )
        bot.reply_to(message, f"Cuenta {message.text} vinculada a la transacción.")
        return ask_file(message)
    ans = bot.reply_to(
        message,
        f"La cuenta {message.text} no se encuentra en la lista de cuentas. Por favor, intente nuevamente con una cuenta aceptable.",
    )
    bot.register_next_step_handler(ans, process_related_account)


# STAGE 6B: Payments and Credits
def process_payment(message):
    process_related_account(message)
    if new_tx["amount"] > 0:
        return next_step(step_routine=2)
    process_tx()


def process_method(message):
    if message.text in pocketsmith_interface.payment_method_list:
        new_tx["payment_method"] = message.text
        bot.reply_to(message, "Método de pago %s aceptado." % new_tx["payment_method"])
        return ask_file(message)
    ans = bot.reply_to(
        message,
        f"El método de pago {message.text} no se encuentra en la lista disponible. Por favor, intente nuevamente con una método aceptable.",
    )
    bot.register_next_step_handler(ans, process_method)


# STAGE 6C: Federal Tax or State Tax
def process_tax(message):
    if message.text in pocketsmith_interface.tax_list:
        new_tx["tax"] = message.text
        ans = bot.reply_to(message, "Impuesto %s aceptado." % new_tx["tax"])
        return next_step(step_routine=3)
    ans = bot.reply_to(
        message,
        f"El impuesto {message.text} no se encuentra en la lista disponible. Por favor, intente nuevamente con un impuesto existente.",
    )
    bot.register_next_step_handler(ans, process_tax)


def process_reference(message):
    new_tx["reference"] = message.text.capitalize()
    ask_file(message)


# STAGE 6D: Crypto


# STAGE 7: ADITIONAL OPTIONS
def filter_ad_options(c) -> bool:
    if c.data in ["installments", "third_party", "none"]:
        return True
    return False


@bot.callback_query_handler(func=filter_ad_options)
def process_aditional_options(c):
    match c.data:
        case "installments":
            next_step(step_routine=4)
        case "third_party":
            if new_tx["amount"] > 0:
                return next_step(step_routine=5)
            if new_tx["amount"] < 0:
                return next_step(step_routine=6)
        case "none":
            next_step()


# STAGE 7A: Installments
def process_installments(message):
    try:
        inst = int(message.text)
        if inst > 1:
            new_tx["installments"] = inst
            bot.reply_to(
                message, "Cantidad de cuotas asignadas %s" % new_tx["installments"]
            )
            return next_step(step_routine=4)
        ans = bot.reply_to(
            message,
            "No se puede seleccionar solo una cuota. El número de cuotas debe ser mayor que 1.",
        )
        bot.register_next_step_handler(ans, process_installments)
    except Exception as e:
        print(e)


# STAGE 7B: Third party
def process_third_party(message):
    if message.text == "*&Nuevo Pagador&*":
        ans = bot.reply_to(message, "¿Como se llama el nuevo comercio?")
        return bot.register_next_step_handler(ans, process_third_party_2)
    if message.text not in pocketsmith_interface.payees_list:
        if new_tx["income"]:
            ans = bot.reply_to(
                message,
                "El comercio no se encuentra en la lista disponible. Utilice la lista validada o agregue uno nuevo.",
            )
        else:
            ans = bot.reply_to(
                message,
                "El responsable no se encuentra en la lista disponible. Utilice la lista validada o agregue uno nuevo.",
            )
        return bot.register_next_step_handler(ans, process_third_party)
    new_tx["third_party"] = message.text
    if new_tx["income"]:
        bot.reply_to(message, "Comercio %s aceptado" % new_tx["third_party"])
        return bot.send_message(
            m_id,
            f"¿En qué fecha se realizó el consumo?\nSeleccione {LSTEP[s_2]}",  # type: ignore
            reply_markup=c_2,
        )
    next_step(step_routine=6)
    bot.reply_to(message, "Responsable %s aceptado" % new_tx["third_party"])


def process_third_party_2(message):
    if message.text.lower() not in [
        x.lower() for x in pocketsmith_interface.payees_list
    ]:
        pocketsmith_interface.addPayee(message.text)
        if new_tx["income"]:
            bot.reply_to(message, "Nuevo comercio %s agregado." % new_tx["third_party"])
        else:
            bot.reply_to(
                message,
                "Nuevo responsable %s agregado." % new_tx["third_party"],
            )
    process_third_party(message)


@bot.callback_query_handler(func=WMonthTelegramCalendar.func(calendar_id=1))
def cal_1(c):
    message = c.message
    if c.data == "cbcal_1select_today":
        result = date.today()
    else:
        result, key, step = WMonthTelegramCalendar().process(c.data)  # type: ignore
    if not result and key:  # type: ignore
        bot.edit_message_text(
            f"Seleccione {LSTEP[step]}",  # type: ignore
            m_id,
            message.message_id,
            reply_markup=key,
        )
    elif result:
        new_tx["date"] = str(result)
    bot.edit_message_text(
        "La fecha seleccionada es %s"
        % datetime.strptime(new_tx["date"], "%Y-%m-%d").strftime("%d-%m-%y"),
        m_id,
        message.message_id,
    )
    next_step(step_routine=5)


# STAGE 8: ATTACHMENTS
def ask_file(message):
    bot.send_message(
        m_id,
        "¿Quiere cargar un comprobante?\nSubalo o presione 'No'",
        reply_markup=quick_markup({"No": {"callback_data": "no_files"}}, row_width=1),
    )
    bot.clear_step_handler(message)


@bot.callback_query_handler(func=lambda c: c.data == "no_files")
def no_files(c):
    bot.send_message(m_id, "No se cargará una imagen.")
    process_tx()


@bot.message_handler(content_types=["photo", "document"])
def file_factory(message):
    if message.photo:
        f = bot.get_file(message.photo[-1].file_id)
    if message.document:
        f = bot.get_file(message.document.file_id)
    tmp_files.append(base64.b64encode(bot.download_file(f.file_path)).decode("ascii"))  # type: ignore
    if files_ans_id == 0:
        ans = bot.send_message(
            m_id,
            f"{len(tmp_files)} archivos cargados.\nSi desea terminar la carga, apriete /done_files",
        )
        files_ans_id = ans.message_id
        return
    bot.edit_message_text(
        f"{len(tmp_files)} archivos cargados.\nSi desea terminar la carga, apriete /done_files",
        m_id,
        files_ans_id,
    )


# STAGE 9: UPLOAD TX TO POCKETSMITH
def getNote():
    new_tx["note"] = pocketsmith_interface.createNote(
        new_tx["category"],
        new_tx["installments"],
        new_tx["third_party"],
        new_tx["related_account"],
        new_tx["payment_method"],
        new_tx["reference"],
        new_tx["tax"],
        new_tx["pair_exchanged"],
        new_tx["income"],
        new_tx["amount"],
        new_tx["tx_date"],
    )


def process_tx():
    new_tx["file"] = tmp_files
    getNote()
    for cat in pocketsmith_interface.categories_list:
        if cat["id"] == new_tx["category"]:
            new_tx["txtype"] = cat["tx"]
    if new_tx["third_party"]:
        new_tx["txtype"] = True
    installment_amount = (
        new_tx["amount"] // new_tx["installments"]
        + new_tx["amount"] % new_tx["installments"]
    )
    r = pocketsmith_interface.uploadTxToPocketsmith(
        new_tx["date"],
        new_tx["payee"],
        installment_amount,
        new_tx["category"],
        new_tx["note"][0],
        new_tx["label"],
        new_tx["txtype"],
        new_tx["account"],
        file=new_tx["file"],
    )
    if r.status_code == 201:
        account_name = pocketsmith_interface.getNameByID(new_tx["account"], "account")
        bot.send_message(
            m_id,
            f"Transacción cargada exitosamente:\n Cuenta: {account_name}\n Pagador: {new_tx['payee']}\n ¿Ingreso?: {new_tx['income']}\n Importe: {new_tx['amount']}\n Categoria: {new_tx['category']}\n Fecha: {new_tx['date']}\n Nota: {new_tx['note'][0]}\n",
        )
    else:
        bot.send_message(
            m_id, "Hubo un error al cargar la transacción. Intente de nuevo."
        )
    if new_tx["installments"] > 1:
        for i in range(1, new_tx["installments"]):
            installment_amount = new_tx["amount"] // new_tx["installments"]
            r = pocketsmith_interface.uploadTxToPocketsmith(
                new_tx["date"],
                new_tx["payee"],
                installment_amount,
                new_tx["category"],
                new_tx["note"][i],
                new_tx["label"],
                new_tx["txtype"],
                new_tx["account"],
            )
            if r.status_code == 201:
                account_name = pocketsmith_interface.getNameByID(
                    new_tx["account"], "account"
                )
                bot.send_message(
                    m_id,
                    f"Transacción cargada exitosamente:\n Cuenta: {account_name}\n Pagador: {new_tx['payee']}\n ¿Ingreso?: {new_tx['income']}\n Importe: {new_tx['amount']}\n Categoria: {new_tx['category']}\n Fecha: {new_tx['date']}\n Nota: {new_tx['note'][i]}\n",
                )
            else:
                bot.send_message(
                    m_id, "Hubo un error al cargar la transacción. Intente de nuevo."
                )


def next_step(step_routine=0):
    ans = bot.send_message(
        m_id,
        STEP[step_routine][current_step[step_routine]][0],
        reply_markup=STEP[step_routine][current_step[step_routine]][1],
    )
    bot.register_next_step_handler(
        ans, STEP[step_routine][current_step[step_routine]][2]
    )
    current_step[step_routine] += 1


STEP = [
    [
        (f"¿En que fecha ocurrió la transacción?\nSeleccione {LSTEP[s_1]}", c_1, None),  # type: ignore
        (
            "¿En qué cuenta se realizó la transacción?",
            quick_markup(
                {
                    "Buscar entre datos validados": {
                        "switch_inline_query_current_chat": "/account "
                    }
                },
                row_width=1,
            ),
            process_account,
        ),
        (
            "¿Como se llama el pagador?",
            quick_markup(
                {
                    "Buscar entre datos validados": {
                        "switch_inline_query_current_chat": "/payee "
                    }
                },
                row_width=1,
            ),
            process_payee_1,
        ),
        (
            "¿Cual es la categoria?",
            quick_markup(
                {
                    "Buscar entre datos validados": {
                        "switch_inline_query_current_chat": "/category "
                    }
                },
                row_width=1,
            ),
            process_category,
        ),
        (
            "¿De cuanto es el importe? (Por defecto la transacción sera un gasto. Si se agrega un '+' al final del importe se categorizará como ingreso)",
            None,
            process_amount,
        ),
        (
            "¿Qué etiqueta quiere eligir?",
            quick_markup(
                {
                    "Buscar entre datos validados": {
                        "switch_inline_query_current_chat": "/label "
                    },
                    "Ninguna": {"callback_data": "cancel_labels"},
                },
                row_width=2,
            ),
            process_label,
        ),
        ("Escriba una referencia para la transacción.", None, process_reference),
    ],
    [
        (
            "¿De/A qué cuenta se realizó la transferencia?",
            quick_markup(
                {
                    "Buscar entre datos validados": {
                        "switch_inline_query_current_chat": "/account "
                    }
                },
                row_width=1,
            ),
            process_related_account,
        ),
    ],
    [
        (
            "¿De/A qué cuenta se realizó el crédito/el pago?",
            quick_markup(
                {
                    "Buscar entre datos validados": {
                        "switch_inline_query_current_chat": "/account "
                    }
                },
                row_width=1,
            ),
            process_payment,
        ),
        (
            "¿Qué método de pago se utilizó?",
            quick_markup(
                {
                    "Buscar entre datos validados": {
                        "switch_inline_query_current_chat": "/payment "
                    }
                },
                row_width=1,
            ),
            process_method,
        ),
    ],
    [
        (
            "¿Cuál es el nombre del impuesto?",
            quick_markup(
                {
                    "Buscar entre datos validados": {
                        "switch_inline_query_current_chat": "/tax "
                    }
                },
                row_width=1,
            ),
            process_tax,
        ),
        ("Escriba una referencia para la transacción.", None, process_reference),
    ],
    [
        ("¿Cuantas cuotas?", None, process_installments),
        ("Escriba una referencia para la transacción.", None, process_reference),
    ],
    [
        (
            "¿Donde se realizo el consumo?",
            quick_markup(
                {
                    "Buscar entre datos validados": {
                        "switch_inline_query_current_chat": "/payee "
                    }
                },
                row_width=1,
            ),
            process_third_party,
        ),
        (
            "¿En que cuenta se realizó el pago relacionado?",
            quick_markup(
                {
                    "Buscar entre datos validados": {
                        "switch_inline_query_current_chat": "/account "
                    }
                },
                row_width=1,
            ),
            process_related_account,
        ),
    ],
    [
        (
            "¿A nombre de quien se realizó el consumo?",
            quick_markup(
                {
                    "Buscar entre datos validados": {
                        "switch_inline_query_current_chat": "/payee "
                    }
                },
                row_width=1,
            ),
            process_third_party,
        ),
        (
            "¿Donde se depositó el crédito correspondiente?",
            quick_markup(
                {
                    "Buscar entre datos validados": {
                        "switch_inline_query_current_chat": "/account "
                    }
                },
                row_width=1,
            ),
            process_related_account,
        ),
    ],
]


@bot.inline_handler(lambda query: "/payee" in re.findall("/payee", query.query))
def query_payee(inline_query):
    search = inline_query.query[7:]
    try:
        options = []
        i = 1
        for p in pocketsmith_interface.payees_list:  # type: ignore
            m = re.search(search.lower(), f"{p.lower()}")
            if not isinstance(m, re.Match):
                continue
            if len(m.group()) > 1:
                options.append(
                    InlineQueryResultArticle(i, p, InputTextMessageContent(p))
                )
                i += 1
        options.append(
            InlineQueryResultArticle(
                i + 1,
                "🆕 Nuevo pagador 🆕",
                InputTextMessageContent("*&Nuevo Pagador&"),
            )
        )
        bot.answer_inline_query(inline_query.id, options, cache_time=1)
    except Exception as e:
        print(e)


@bot.inline_handler(lambda query: "/category" in re.findall("/category", query.query))
def query_category(inline_query):
    search = inline_query.query[10:]
    try:
        options = []
        i = 1
        for p in pocketsmith_interface.categories_list:
            p_name = p["name"]
            m = re.search(search.lower(), f"{p_name.lower()}")
            if not isinstance(m, re.Match):
                continue
            if len(m.group()) > 1:
                options.append(
                    InlineQueryResultArticle(i, p_name, InputTextMessageContent(p_name))
                )
                i += 1
        bot.answer_inline_query(inline_query.id, options, cache_time=1)
    except Exception as e:
        print(e)


@bot.inline_handler(lambda query: "/account" in re.findall("/account", query.query))
def query_account(inline_query):
    search = inline_query.query[10:]
    try:
        options = []
        i = 1
        for p in pocketsmith_interface.accounts_list:
            p_name = p["name"]
            m = re.search(search.lower(), f"{p_name.lower()}")
            if not isinstance(m, re.Match):
                continue
            if len(m.group()) > 1:
                url = WEBHOOK_URL_BASE + WEBHOOK_URL_PATH + p["thumbnail"]
                options.append(
                    InlineQueryResultArticle(
                        i,
                        p_name,
                        InputTextMessageContent(p_name),
                        thumbnail_url=url,
                        thumbnail_height=100,
                        thumbnail_width=100,
                    )
                )
                i += 1
        bot.answer_inline_query(inline_query.id, options, cache_time=1)
    except Exception as e:
        print(e)


@bot.inline_handler(lambda query: "/label" in re.findall("/label", query.query))
def query_label(inline_query):
    search = inline_query.query[7:]
    try:
        options = []
        i = 1
        for p in pocketsmith_interface.labels_list:
            m = re.search(search.lower(), f"{p.lower()}")
            if not isinstance(m, re.Match):
                continue
            if len(m.group()) > 1:
                options.append(
                    InlineQueryResultArticle(i, p, InputTextMessageContent(p))
                )
                i += 1
        bot.answer_inline_query(inline_query.id, options, cache_time=1)
    except Exception as e:
        print(e)


@bot.inline_handler(lambda query: "/payment" in re.findall("/payment", query.query))
def query_payment(inline_query):
    search = inline_query.query[9:]
    try:
        options = []
        i = 1
        for p in pocketsmith_interface.payment_method_list:
            m = re.search(search.lower(), f"{p.lower()}")
            if not isinstance(m, re.Match):
                continue
            if len(m.group()) > 1:
                options.append(
                    InlineQueryResultArticle(i, p, InputTextMessageContent(p))
                )
                i += 1
        bot.answer_inline_query(inline_query.id, options, cache_time=1)
    except Exception as e:
        print(e)


@bot.inline_handler(lambda query: "/tax" in re.findall("/tax", query.query))
def query_tax(inline_query):
    search = inline_query.query[5:]
    try:
        options = []
        i = 1
        for p in pocketsmith_interface.tax_list:
            m = re.search(search.lower(), f"{p.lower()}")
            if not isinstance(m, re.Match):
                continue
            if len(m.group()) > 1:
                options.append(
                    InlineQueryResultArticle(i, p, InputTextMessageContent(p))
                )
                i += 1
        bot.answer_inline_query(inline_query.id, options, cache_time=1)
    except Exception as e:
        print(e)
