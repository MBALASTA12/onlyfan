from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
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
    {"name": "Agustina Alexia", "photo": "https://raw.githubusercontent.com/MBALASTA12/onlyfan/main/photo/Profile.PNG", "price": 5.00},
    {"name": "Pia", "photo": "https://raw.githubusercontent.com/MBALASTA12/onlyfan/main/photo/profile.jpg", "price": 10.00},
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

bot = Bot(token=os.environ["BOT_API_TOKEN"])

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

        # Get the user ID from the custom field
        user_id = ipn_data.get("custom", None)

        # Send a message to the user directly in Telegram
        if user_id:
            try:
                message = "Hi! Your payment has been successfully processed. Thank you for subscribing!"
                bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                logger.error(f"Error sending message to user: {e}")

        return jsonify({"message": "Payment verified and processed."})
    else:
        logger.error(f"Payment verification FAILED: {ipn_data}")
        return jsonify({"message": "Payment verification failed."})

@app.route("/test_ipn")
def test_ipn():
    from telegram import Bot
    bot = Bot(token=os.environ["BOT_API_TOKEN"])

    # Replace with your own Telegram user ID
    test_user_id = 6793648677  

    try:
        bot.send_message(chat_id=test_user_id, text="✅ Test: Your payment has been successfully processed.")
        return "✅ Test message sent to your Telegram account!"
    except Exception as e:
        return f"❌ Failed to send message: {e}"



async def start(update: Update, context: CallbackContext) -> None:
    for model in models:
        button = InlineKeyboardButton(
            text=f"Subscribe to {model['name']}",
            callback_data=f"subscribe_{model['name']}"
        )
        keyboard = [[button]]
        try:
            # Send message with both caption and photo
            await update.message.reply_photo(
                photo=model['photo'],
                caption=f"{model['name']}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            print(f"User ID: {update.message.from_user.id}")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    model_name = query.data.split("_")[1]  # Extract model name from callback data
    user_id = query.from_user.id

    # Find the model data (including price) for the selected model
    selected_model = next((model for model in models if model["name"] == model_name), None)
    if selected_model:
        model_price = selected_model["price"]
    else:
        model_price = 1.00  # Default price if model not found (can be updated)

    # Create the PayPal payment link with dynamic pricing
    payment_url = (
        f"https://www.paypal.com/cgi-bin/webscr"
        f"?cmd=_xclick&business={PAYPAL_EMAIL}"
        f"&item_name=Subscription+to+{model_name}"
        f"&amount={model_price:.2f}&currency_code=USD"
        f"&notify_url={PAYPAL_IPN_URL}"
        f"&custom={user_id}"
    )

    # Create an inline button that links directly to the PayPal payment page
    payment_button = InlineKeyboardButton(text=f"Pay {model_price:.2f} USD", url=payment_url)
    keyboard = InlineKeyboardMarkup([[payment_button]])

    try:
        message = f"You've subscribed to {model_name}!\n\nClick below to proceed with payment."

        # Check if the message contains text or caption and edit accordingly
        if query.message.text:
            await query.edit_message_text(text=message, reply_markup=keyboard)
        elif query.message.caption:
            await query.edit_message_caption(caption=message, reply_markup=keyboard)
        else:
            # Fallback message if neither text nor caption exists
            await query.message.reply_text(message, reply_markup=keyboard)
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
