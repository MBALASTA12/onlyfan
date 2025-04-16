from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, ContextTypes
import os
from flask import Flask, request, jsonify
import requests
import logging
from threading import Thread

# Replace this with your PayPal LIVE business email
PAYPAL_EMAIL = "abastasjeogeel12@gmail.com"  # <-- UPDATE THIS
PAYPAL_IPN_URL = "https://onlyfan-6cc5a61b58dd.herokuapp.com/ipn"

models = [
    {"name": "Agustina Alexia", "photo": "https://raw.githubusercontent.com/MBALASTA12/onlyfan/main/photo/Profile.PNG"},
    {"name": "Pia", "photo": "https://raw.githubusercontent.com/MBALASTA12/onlyfan/main/photo/profile.jpg"},
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/ipn", methods=["POST"])
def ipn():
    ipn_data = request.form.to_dict()
    verification_url = "https://ipnpb.paypal.com/cgi-bin/webscr"  # LIVE endpoint
    verification_data = {
        "cmd": "_notify-validate",
        **ipn_data
    }
    response = requests.post(verification_url, data=verification_data)
    if response.text == "VERIFIED":
        logger.info(f"Payment VERIFIED: {ipn_data}")
        return jsonify({"message": "Payment verified and processed."})
    else:
        logger.error(f"Payment verification FAILED: {ipn_data}")
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

    model_name = query.data.split("_")[1]
    user_id = query.from_user.id

    # Direct PayPal payment link
    payment_url = (
        f"https://www.paypal.com/cgi-bin/webscr"
        f"?cmd=_xclick&business={PAYPAL_EMAIL}"
        f"&item_name=Subscription+to+{model_name}"
        f"&amount=1.00&currency_code=USD"
        f"&notify_url={PAYPAL_IPN_URL}"
        f"&custom={user_id}"
    )

    try:
        message = f"You've subscribed to {model_name}!\n\nProceed with payment: {payment_url}"
        if query.message.text:
            await query.edit_message_text(text=message)
        elif query.message.caption:
            await query.edit_message_caption(caption=message)
        else:
            await query.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error editing message: {e}")


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
