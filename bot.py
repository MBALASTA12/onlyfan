import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    ContextTypes
)
from threading import Thread
import requests
from dotenv import load_dotenv

# Load .env variables
load_dotenv()
BOT_TOKEN = os.environ["BOT_API_TOKEN"]
PAYPAL_EMAIL = os.environ["PAYPAL_EMAIL"]
PAYPAL_IPN_URL = "https://onlyfan-6cc5a61b58dd.herokuapp.com/ipn"  # CHANGE to your live domain/IPN URL

# Sample model list
models = [
    {"name": "Agustina Alexia", "photo": "https://raw.githubusercontent.com/MBALASTA12/onlyfan/main/photo/Profile.PNG"},
    {"name": "Pia", "photo": "https://raw.githubusercontent.com/MBALASTA12/onlyfan/main/photo/profile.jpg"},
]

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

@app.route("/ipn", methods=["POST"])
def ipn():
    ipn_data = request.form.to_dict()
    verification_url = "https://ipnpb.paypal.com/cgi-bin/webscr"  # ✅ Live IPN URL
    verification_data = {"cmd": "_notify-validate", **ipn_data}

    # Verify IPN
    response = requests.post(verification_url, data=verification_data)
    if response.text == "VERIFIED":
        payment_status = ipn_data.get("payment_status")
        receiver_email = ipn_data.get("receiver_email")
        custom_user_id = ipn_data.get("custom")
        amount = ipn_data.get("mc_gross")

        if payment_status == "Completed" and receiver_email == PAYPAL_EMAIL:
            message = f"✅ Payment of ${amount} received successfully! Thank you!"
            requests.post(TELEGRAM_API, data={"chat_id": custom_user_id, "text": message})
            return jsonify({"message": "Payment verified and processed."})
        else:
            return jsonify({"message": "Payment not completed or invalid email."}), 400
    return jsonify({"message": "IPN Verification Failed"}), 400

# Telegram Bot handlers
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
                caption=model['name'],
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except:
            await update.message.reply_text(f"Image for {model['name']} could not be loaded.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    model_name = query.data.split("_")[1]

    # ✅ Live PayPal payment link
    payment_url = (
        f"https://www.paypal.com/cgi-bin/webscr"
        f"?cmd=_xclick&business={PAYPAL_EMAIL}"
        f"&item_name=Subscription+to+{model_name}"
        f"&amount=1.00&currency_code=USD"
        f"&notify_url={PAYPAL_IPN_URL}"
        f"&custom={query.from_user.id}"
    )

    try:
        if query.message.caption:
            await query.edit_message_caption(caption=f"You've subscribed to {model_name}!\nPlease pay here:\n{payment_url}")
        else:
            await query.message.reply_text(f"You've subscribed to {model_name}!\nPlease pay here:\n{payment_url}")
    except Exception as e:
        print(f"Error editing message: {e}")

# Start bot
def start_telegram_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

# Run server + bot
def main():
    port = int(os.environ.get("PORT", 5000))
    thread = Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": port})
    thread.start()
    start_telegram_bot()

if __name__ == "__main__":
    main()
