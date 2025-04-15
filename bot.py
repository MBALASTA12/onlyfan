from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
import os
from flask import Flask, request, jsonify
import requests
import logging
from threading import Thread

models = [
    {"name": "Agustina Alexia", "photo": r"https://raw.githubusercontent.com/MBALASTA12/onlyfan/main/photo/Profile.PNG"},
    {"name": "Pia", "photo": r"https://raw.githubusercontent.com/MBALASTA12/onlyfan/main/photo/profile.jpg"},
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

PAYPAL_IPN_URL = "https://onlyfan-6cc5a61b58dd.herokuapp.com/ipn"

@app.route("/ipn", methods=["POST"])
def ipn():
    ipn_data = request.form.to_dict()
    verification_url = "https://ipnpb.sandbox.paypal.com/cgi-bin/webscr"
    verification_data = {
        "cmd": "_notify-validate",
        **ipn_data
    }
    response = requests.post(verification_url, data=verification_data)
    if response.text == "VERIFIED":
        logger.info("Payment verified")
        return jsonify({"message": "Payment verified and processed."})
    else:
        logger.error("Payment verification failed")
        return jsonify({"message": "Payment verification failed."})

async def start(update: Update, context: CallbackContext) -> None:
    for model in models:
        button = InlineKeyboardButton(
            text=f"Subscribe to {model['name']}",
            callback_data=f"subscribe_{model['name']}"
        )
        keyboard = [[button]]
        try:
            await update.message.reply_photo(
                photo=model['photo'],
                caption=f"{model['name']}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except:
            await update.message.reply_text(f"Image for {model['name']} could not be loaded.")

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    if query.data.startswith("subscribe_"):
        model_name = query.data.split('_', 1)[1]
        await query.edit_message_text(text=f"You've subscribed to {model_name}!")

def start_telegram_bot():
    application = Application.builder().token(os.environ["BOT_API_TOKEN"]).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

def main():
    port = int(os.environ.get("PORT", 5000))
    thread = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': port})
    thread.start()
    start_telegram_bot()

if __name__ == '__main__':
    main()
