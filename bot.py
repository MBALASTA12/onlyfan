from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, ContextTypes
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

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    model_name = query.data.split("_")[1]  # Extract model name from callback data
    payment_url = f"https://www.paypal.com/sdk/js?client-id=BAA9knP12hxopme72RoJs8AnrcJaEqAv5X3Rqvdo1jXxFuuw49PT9wgBCaj2YQMPXg-Znub9Vt6ZnOf85s&components=hosted-buttons&disable-funding=venmo&currency=USD&button-id=GN3XVM23THZGE"

    try:
        if query.message.text:
            # Edit message text to confirm subscription
            await query.edit_message_text(text=f"You've subscribed to {model_name}! Please proceed with payment: {payment_url}")
        elif query.message.caption:
            # Edit caption to confirm subscription
            await query.edit_message_caption(caption=f"You've subscribed to {model_name}! Please proceed with payment: {payment_url}")
        else:
            # Fallback message
            await query.message.reply_text(f"You've subscribed to {model_name}! Please proceed with payment: {payment_url}")
    except Exception as e:
        print(f"Error editing message: {e}")


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
