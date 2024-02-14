import telebot
import flask
from gevent.pywsgi import WSGIServer
from init import WEBHOOK_URL_PATH, WEBHOOK_LISTEN, WEBHOOK_SSL_PRIV, WEBHOOK_SSL_CERT
import bot

app = flask.Flask(__name__)


# Empty webserver index, return nothing, just http 200
@app.route(WEBHOOK_URL_PATH + "<thumbnail>", methods=["GET"])
def index(thumbnail):
    return flask.send_file(f"./account_thumbnails/{thumbnail}")


# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=["POST"])
def webhook():
    if flask.request.headers.get("content-type") == "application/json":
        json_string = flask.request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.bot.process_new_updates([update])  # type: ignore
        return ""
    else:
        flask.abort(403)


if __name__ == "__main__":
    # Production
    http_server = WSGIServer(
        (WEBHOOK_LISTEN, 443),
        app,
        keyfile=WEBHOOK_SSL_PRIV,
        certfile=WEBHOOK_SSL_CERT,
    )
    http_server.serve_forever()
